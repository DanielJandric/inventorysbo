"""
AI Services module for OpenAI integration, chatbot, and semantic search.
"""

import os
import json
import logging
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import OpenAI
from core.app_config import Config
from core.models import CollectionItem, ChatMessage
from core.database import db_manager
from gpt5_compat import from_responses_simple, extract_output_text

logger = logging.getLogger(__name__)


class SmartCache:
    """Multi-level intelligent cache system"""
    
    def __init__(self):
        self._caches = {
            'items': {'data': None, 'timestamp': None, 'ttl': 60},
            'analytics': {'data': None, 'timestamp': None, 'ttl': 300},
            'ai_responses': {'data': {}, 'timestamp': None, 'ttl': 900},
            'embeddings': {'data': {}, 'timestamp': None, 'ttl': 3600}
        }
    
    def get(self, cache_name: str, key: str = 'default'):
        """Get from cache"""
        if cache_name not in self._caches:
            return None
        
        cache_info = self._caches[cache_name]
        now = datetime.now()
        
        if cache_info['timestamp'] and (now - cache_info['timestamp']).seconds < cache_info['ttl']:
            if cache_name in ['ai_responses', 'embeddings']:
                return cache_info['data'].get(key)
            return cache_info['data']
        
        return None
    
    def set(self, cache_name: str, data: Any, key: str = 'default'):
        """Store in cache"""
        if cache_name not in self._caches:
            return
        
        if cache_name in ['ai_responses', 'embeddings']:
            if not isinstance(self._caches[cache_name]['data'], dict):
                self._caches[cache_name]['data'] = {}
            self._caches[cache_name]['data'][key] = data
        else:
            self._caches[cache_name]['data'] = data
        
        self._caches[cache_name]['timestamp'] = datetime.now()
    
    def invalidate(self, cache_name: str = None):
        """Invalidate cache"""
        if cache_name:
            if cache_name in self._caches:
                self._caches[cache_name]['data'] = None if cache_name not in ['ai_responses', 'embeddings'] else {}
                self._caches[cache_name]['timestamp'] = None
        else:
            for cache_info in self._caches.values():
                cache_info['data'] = None
                cache_info['timestamp'] = None


class SemanticSearchRAG:
    """Semantic search engine with RAG"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.embedding_model = "text-embedding-3-small"
    
    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for a query"""
        if not self.client:
            return None
        
        try:
            response = self.client.embeddings.create(
                input=query,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def semantic_search(self, query: str, items: List[CollectionItem], top_k: int = 10) -> List[Tuple[CollectionItem, float]]:
        """Hybrid semantic search: embeddings + TF-IDF BM25-like fusion"""
        # 1) Embedding route
        embedding_scores: List[Tuple[CollectionItem, float]] = []
        try:
            query_embedding = self.get_query_embedding(query)
            if query_embedding:
                items_with_embeddings = [item for item in items if item.embedding]
                for item in items_with_embeddings:
                    try:
                        s = self._cosine_similarity(query_embedding, item.embedding)
                        embedding_scores.append((item, float(s)))
                    except Exception:
                        continue
        except Exception:
            pass

        # 2) Sparse route (TF-IDF as a simple BM25-ish proxy)
        sparse_scores: List[Tuple[CollectionItem, float]] = []
        try:
            corpus = []
            corpus_items = []
            for it in items:
                parts = [it.name or "", it.category or "", it.description or ""]
                if it.category == 'Actions':
                    parts.extend([
                        it.stock_symbol or "",
                        it.stock_exchange or "",
                    ])
                doc = " ".join(parts).lower()
                corpus.append(doc)
                corpus_items.append(it)
            
            if corpus:
                vectorizer = TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=5000,
                    stop_words='english'
                )
                tfidf_matrix = vectorizer.fit_transform(corpus)
                query_vec = vectorizer.transform([query.lower()])
                scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
                
                for i, score in enumerate(scores):
                    if score > 0:
                        sparse_scores.append((corpus_items[i], float(score)))
        except Exception:
            pass

        # 3) Fusion with score normalization
        all_scores = {}
        
        # Add embedding scores
        for item, score in embedding_scores:
            all_scores[item.id] = {'item': item, 'embedding_score': score, 'sparse_score': 0}
        
        # Add sparse scores
        for item, score in sparse_scores:
            if item.id in all_scores:
                all_scores[item.id]['sparse_score'] = score
            else:
                all_scores[item.id] = {'item': item, 'embedding_score': 0, 'sparse_score': score}
        
        # Combine scores (weighted average)
        final_scores = []
        for data in all_scores.values():
            # Weight: 60% embedding, 40% sparse
            combined_score = (0.6 * data['embedding_score']) + (0.4 * data['sparse_score'])
            final_scores.append((data['item'], combined_score))
        
        # Sort by score and return top_k
        final_scores.sort(key=lambda x: x[1], reverse=True)
        return final_scores[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class AIService:
    """Main AI service for chatbot and AI operations"""
    
    def __init__(self):
        self.client = None
        self.semantic_search = None
        self.cache = SmartCache()
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        if Config.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.semantic_search = SemanticSearchRAG(self.client)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.semantic_search:
            return None
        return self.semantic_search.get_query_embedding(text)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not self.client:
            return [None] * len(texts)
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    def chat_completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs):
        """Generate chat completion"""
        if not self.client:
            return None
        
        try:
            return self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-4o-mini'),
                messages=messages,
                stream=stream,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return None
    
    def process_chatbot_query(self, query: str, conversation_id: str, items: List[CollectionItem]) -> Dict[str, Any]:
        """Process a chatbot query with RAG"""
        # Check cache
        cache_key = hashlib.md5(f"{query}:{conversation_id}".encode()).hexdigest()
        cached_response = self.cache.get('ai_responses', cache_key)
        if cached_response:
            return cached_response
        
        # Perform semantic search
        relevant_items = []
        if self.semantic_search and items:
            search_results = self.semantic_search.semantic_search(query, items, top_k=5)
            relevant_items = [item for item, _ in search_results]
        
        # Build context
        context = self._build_context(relevant_items)
        
        # Generate response
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        
        response = self.chat_completion(messages)
        
        if response:
            result = {
                'response': response.choices[0].message.content,
                'relevant_items': [item.to_dict() for item in relevant_items],
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache response
            self.cache.set('ai_responses', result, cache_key)
            
            # Save to database
            db_manager.save_chat_message(
                conversation_id,
                'user',
                query,
                {'relevant_items': len(relevant_items)}
            )
            db_manager.save_chat_message(
                conversation_id,
                'assistant',
                result['response']
            )
            
            return result
        
        return {
            'response': "I'm sorry, I couldn't process your query at this time.",
            'relevant_items': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _build_context(self, items: List[CollectionItem]) -> str:
        """Build context from relevant items"""
        if not items:
            return "No specific items found related to your query."
        
        context_parts = []
        for item in items[:5]:  # Limit to top 5 items
            parts = [f"- {item.name} ({item.category})"]
            if item.description:
                parts.append(f"  Description: {item.description}")
            if item.current_value:
                parts.append(f"  Value: CHF {item.current_value:,.2f}")
            if item.status:
                parts.append(f"  Status: {item.status}")
            if item.stock_symbol:
                parts.append(f"  Stock: {item.stock_symbol}")
            context_parts.append("\n".join(parts))
        
        return "\n\n".join(context_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for chatbot"""
        return """You are an AI assistant for a private collection management system. 
        You help users understand and analyze their collection of vehicles, stocks, real estate, and other assets.
        Provide helpful, accurate, and concise responses based on the context provided.
        If you don't have specific information, say so clearly."""
    
    def analyze_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data using AI"""
        if not self.client:
            return {'error': 'AI service not available'}
        
        try:
            prompt = f"""Analyze the following market data and provide insights:
            {json.dumps(data, indent=2)}
            
            Provide:
            1. Key trends
            2. Notable changes
            3. Risk factors
            4. Recommendations"""
            
            response = self.chat_completion([
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                return {
                    'analysis': response.choices[0].message.content,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error analyzing market data: {e}")
        
        return {'error': 'Failed to analyze market data'}
    
    def generate_market_briefing(self, market_data: Dict[str, Any]) -> str:
        """Generate a market briefing using AI"""
        if not self.client:
            return "Market briefing unavailable"
        
        try:
            # Use GPT-5 compatibility layer if available
            response = from_responses_simple(
                prompt=f"Generate a concise market briefing: {json.dumps(market_data)}",
                max_new_tokens=500
            )
            
            if response:
                return extract_output_text(response)
            
            # Fallback to standard completion
            response = self.chat_completion([
                {"role": "system", "content": "You are a financial market analyst."},
                {"role": "user", "content": f"Generate a concise market briefing: {json.dumps(market_data)}"}
            ])
            
            if response:
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating market briefing: {e}")
        
        return "Unable to generate market briefing at this time."


# Create singleton instance
ai_service = AIService()