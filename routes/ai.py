"""
Routes for AI and chatbot functionality.
"""

import json
import uuid
import hashlib
import logging
from flask import Blueprint, jsonify, request, Response, stream_with_context
from typing import Dict, Any
from datetime import datetime
from core.database import db_manager
from core.models import CollectionItem
from services.ai_service import ai_service
from core.utils import generate_cache_key

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api')


@ai_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """Main chatbot endpoint"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        # Check if AI service is available
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service is not available'
            }), 503
        
        # Get all items for context
        items_data = db_manager.get_all_items()
        items = [CollectionItem.from_dict(item) for item in items_data]
        
        # Process the query
        result = ai_service.process_chatbot_query(
            user_message,
            conversation_id,
            items
        )
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'conversation_id': conversation_id,
            'relevant_items': result.get('relevant_items', []),
            'timestamp': result['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/chatbot/stream', methods=['POST'])
def chatbot_stream():
    """Streaming chatbot endpoint"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        # Check if AI service is available
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service is not available'
            }), 503
        
        def generate():
            """Generate streaming response"""
            try:
                # Get context
                items_data = db_manager.get_all_items()
                items = [CollectionItem.from_dict(item) for item in items_data]
                
                # Perform semantic search
                relevant_items = []
                if ai_service.semantic_search and items:
                    search_results = ai_service.semantic_search.semantic_search(
                        user_message, items, top_k=5
                    )
                    relevant_items = [item for item, _ in search_results]
                
                # Build context
                context = ai_service._build_context(relevant_items)
                
                # Create messages
                messages = [
                    {"role": "system", "content": ai_service._get_system_prompt()},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_message}"}
                ]
                
                # Stream response
                response = ai_service.chat_completion(messages, stream=True)
                
                if response:
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
                
                # Send final message with metadata
                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming chatbot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/embeddings/generate', methods=['POST'])
def generate_embeddings():
    """Generate embeddings for items"""
    try:
        data = request.json
        item_ids = data.get('item_ids', []) if data else []
        
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service is not available'
            }), 503
        
        # Get items
        if item_ids:
            items = [db_manager.get_item_by_id(item_id) for item_id in item_ids]
            items = [item for item in items if item]
        else:
            items = db_manager.get_all_items()
        
        if not items:
            return jsonify({
                'success': False,
                'error': 'No items found'
            }), 404
        
        # Generate embeddings
        updated_count = 0
        failed_count = 0
        
        for item in items:
            try:
                # Create text for embedding
                text_parts = [
                    item.get('name', ''),
                    item.get('category', ''),
                    item.get('description', ''),
                    item.get('status', '')
                ]
                
                if item.get('stock_symbol'):
                    text_parts.append(item['stock_symbol'])
                
                text = ' '.join(filter(None, text_parts))
                
                # Generate embedding
                embedding = ai_service.generate_embedding(text)
                
                if embedding:
                    # Update in database
                    success = db_manager.update_item_embedding(item['id'], embedding)
                    if success:
                        updated_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error generating embedding for item {item.get('id')}: {e}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'updated': updated_count,
            'failed': failed_count,
            'total': len(items)
        })
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/embeddings/status', methods=['GET'])
def embeddings_status():
    """Get embeddings status"""
    try:
        all_items = db_manager.get_all_items()
        items_with_embeddings = db_manager.get_items_with_embeddings()
        
        return jsonify({
            'success': True,
            'total_items': len(all_items),
            'items_with_embeddings': len(items_with_embeddings),
            'coverage_percentage': (len(items_with_embeddings) / len(all_items) * 100) if all_items else 0,
            'ai_service_available': ai_service.is_available()
        })
        
    except Exception as e:
        logger.error(f"Error getting embeddings status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/ai-update-price/<int:item_id>', methods=['POST'])
def ai_update_price(item_id: int):
    """Update item price using AI analysis"""
    try:
        item = db_manager.get_item_by_id(item_id)
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
        
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service is not available'
            }), 503
        
        # Prepare item data for analysis
        analysis_data = {
            'name': item.get('name'),
            'category': item.get('category'),
            'description': item.get('description'),
            'construction_year': item.get('construction_year'),
            'condition': item.get('condition'),
            'current_value': item.get('current_value'),
            'acquisition_price': item.get('acquisition_price')
        }
        
        # Get AI market analysis
        market_analysis = ai_service.analyze_market_data(analysis_data)
        
        if 'error' in market_analysis:
            return jsonify({
                'success': False,
                'error': market_analysis['error']
            }), 500
        
        # Extract suggested price from analysis
        # This is a simplified example - you'd need more sophisticated parsing
        analysis_text = market_analysis.get('analysis', '')
        
        # Update item with AI insights
        update_data = {
            'ai_analysis': analysis_text,
            'ai_analysis_date': datetime.now().isoformat()
        }
        
        updated_item = db_manager.update_item(item_id, update_data)
        
        return jsonify({
            'success': True,
            'item': updated_item,
            'analysis': analysis_text
        })
        
    except Exception as e:
        logger.error(f"Error in AI price update for item {item_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/ai-update-all-vehicles', methods=['POST'])
def ai_update_all_vehicles():
    """Update all vehicle prices using AI"""
    try:
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service is not available'
            }), 503
        
        # Get all vehicles
        vehicles = db_manager.get_items_by_category('Véhicules')
        
        if not vehicles:
            return jsonify({
                'success': False,
                'error': 'No vehicles found'
            }), 404
        
        updated_count = 0
        failed_count = 0
        results = []
        
        for vehicle in vehicles:
            try:
                # Prepare data for analysis
                analysis_data = {
                    'name': vehicle.get('name'),
                    'construction_year': vehicle.get('construction_year'),
                    'condition': vehicle.get('condition'),
                    'current_value': vehicle.get('current_value')
                }
                
                # Get AI analysis
                market_analysis = ai_service.analyze_market_data(analysis_data)
                
                if 'error' not in market_analysis:
                    # Update vehicle
                    update_data = {
                        'ai_analysis': market_analysis.get('analysis'),
                        'ai_analysis_date': datetime.now().isoformat()
                    }
                    
                    if db_manager.update_item(vehicle['id'], update_data):
                        updated_count += 1
                        results.append({
                            'id': vehicle['id'],
                            'name': vehicle['name'],
                            'status': 'updated'
                        })
                    else:
                        failed_count += 1
                        results.append({
                            'id': vehicle['id'],
                            'name': vehicle['name'],
                            'status': 'failed'
                        })
                else:
                    failed_count += 1
                    results.append({
                        'id': vehicle['id'],
                        'name': vehicle['name'],
                        'status': 'error',
                        'error': market_analysis['error']
                    })
                    
            except Exception as e:
                logger.error(f"Error updating vehicle {vehicle.get('id')}: {e}")
                failed_count += 1
                results.append({
                    'id': vehicle.get('id'),
                    'name': vehicle.get('name'),
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'updated': updated_count,
            'failed': failed_count,
            'total': len(vehicles),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error updating all vehicles: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/chatbot/metrics', methods=['GET'])
def get_chatbot_metrics():
    """Get chatbot usage metrics"""
    try:
        # This would typically query a metrics database
        # For now, return sample metrics
        return jsonify({
            'success': True,
            'metrics': {
                'total_conversations': 0,
                'total_messages': 0,
                'average_response_time': 0,
                'ai_service_status': 'available' if ai_service.is_available() else 'unavailable',
                'cache_hit_rate': 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chatbot metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500