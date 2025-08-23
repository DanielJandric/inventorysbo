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
    """Update item price using sophisticated AI market analysis - matches original app"""
    try:
        if not ai_service.is_available():
            return jsonify({'error': 'Moteur IA Indisponible'}), 503
        
        # Get the target item
        items_data = db_manager.get_all_items()
        items = [CollectionItem.from_dict(item) for item in items_data]
        target_item = next((item for item in items if item.id == item_id), None)
        
        if not target_item:
            return jsonify({'error': 'Objet non trouvé'}), 404
        
        # Check if it's a stock (not allowed for AI pricing)
        if target_item.category == 'Actions':
            return jsonify({
                'error': 'Cette fonction est réservée aux véhicules. Utilisez la mise à jour des prix d\'actions pour les actions.'
            }), 400
        
        # Find similar items for context
        similar_items = [i for i in items if i.category == target_item.category and i.id != item_id]
        
        # Get items with prices and construction years for similarity scoring
        similar_items_with_prices = [
            i for i in similar_items 
            if (i.sold_price or i.current_value) and i.construction_year
        ]
        
        # Calculate similarity score based on year and category
        def similarity_score(item):
            score = 100
            if target_item.construction_year and item.construction_year:
                year_diff = abs(target_item.construction_year - item.construction_year)
                score -= year_diff * 2  # 2 point penalty per year difference
            return score
        
        # Sort by similarity score and get top 3
        similar_items_sorted = sorted(similar_items_with_prices, key=similarity_score, reverse=True)
        top_3_similar = similar_items_sorted[:3]
        
        # Build context of 3 similar objects
        similar_context = ""
        if top_3_similar:
            similar_context = "\n\nOBJETS SIMILAIRES DANS LA COLLECTION:"
            for i, similar_item in enumerate(top_3_similar, 1):
                price = similar_item.sold_price or similar_item.current_value
                status = "Vendu" if similar_item.sold_price else "valeur actuelle"
                similar_context += f"\n{i}. {similar_item.name} ({similar_item.construction_year or 'N/A'}) - {status}: {price:,.0f} CHF"
                if similar_item.description:
                    similar_context += f" - {similar_item.description[:80]}..."
        
        # Create comprehensive prompt for AI estimation
        prompt = f"""Estime le prix de marché actuel de cet objet en CHF en te basant sur le marché réel :

OBJET À ÉVALUER:
- Nom: {target_item.name}
- Catégorie: {target_item.category}
- Année: {target_item.construction_year or 'N/A'}
- État: {target_item.condition or 'N/A'}
- Description: {target_item.description or 'N/A'}
{similar_context}

INSTRUCTIONS IMPORTANTES:
1. Recherche les prix actuels du marché pour ce modèle exact ou des modèles très similaires
2. Utilise tes connaissances du marché automobile/horloger/immobilier actuel
3. Compare avec des ventes récentes d'objets similaires sur le marché (pas dans ma collection)
4. Prends en compte l'année, l'état et les spécificités du modèle
Pour les voitures : considère les sites comme AutoScout24, Comparis, annonces spécialisées
Pour les montres : marché des montres d'occasion, chrono24, enchères récentes
Pour l'immobilier : prix au m² dans la région, transactions récentes

Réponds en JSON avec:
- estimated_price (nombre en CHF basé sur le marché actuel)
- reasoning (explication détaillée en français avec références de marché)
- confidence_score (0.1-0.9)
- market_trend (hausse/stable/baisse)"""
        
        # Get AI market analysis using sophisticated prompt
        market_analysis = ai_service.get_sophisticated_price_estimate(prompt)
        
        if 'error' in market_analysis:
            return jsonify({'error': market_analysis['error']}), 500
        
        estimated_price = market_analysis.get('estimated_price')
        if not estimated_price or estimated_price <= 0:
            return jsonify({'error': 'Estimation IA invalide'}), 400
        
        # Update item with estimated price
        update_data = {
            'current_value': estimated_price,
            'last_action_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        updated_item = db_manager.update_item(item_id, update_data)
        
        if updated_item:
            logger.info(f"✅ Prix IA mis à jour pour {target_item.name}: {estimated_price:,.0f} CHF")
            
            return jsonify({
                'success': True,
                'message': f'Prix mis à jour avec succès: {estimated_price:,.0f} CHF',
                'updated_price': estimated_price,
                'ai_estimation': market_analysis,
                'item_name': target_item.name
            })
        else:
            return jsonify({'error': 'Erreur lors de la mise à jour en base de données'}), 500
        
    except Exception as e:
        logger.error(f"Error in AI price update for item {item_id}: {e}")
        return jsonify({'error': 'Erreur lors de la mise à jour IA'}), 500


@ai_bp.route('/ai-update-all-vehicles', methods=['POST'])
def ai_update_all_vehicles():
    """Update all vehicle prices using sophisticated AI - matches original app"""
    try:
        if not ai_service.is_available():
            return jsonify({'error': 'Moteur IA Indisponible'}), 503
        
        # Get all vehicles (not stocks)
        vehicles_data = db_manager.get_items_by_category('Véhicules')
        vehicles = [CollectionItem.from_dict(vehicle) for vehicle in vehicles_data]
        
        if not vehicles:
            return jsonify({'error': 'Aucun véhicule trouvé'}), 404
        
        updated_count = 0
        failed_count = 0
        results = []
        
        for vehicle in vehicles:
            try:
                # Get all items for context (same as single item update)
                all_items_data = db_manager.get_all_items()
                all_items = [CollectionItem.from_dict(item) for item in all_items_data]
                
                # Find similar vehicles for context
                similar_vehicles = [i for i in all_items if i.category == 'Véhicules' and i.id != vehicle.id]
                similar_vehicles_with_prices = [
                    i for i in similar_vehicles 
                    if (i.sold_price or i.current_value) and i.construction_year
                ]
                
                # Calculate similarity score
                def similarity_score(item):
                    score = 100
                    if vehicle.construction_year and item.construction_year:
                        year_diff = abs(vehicle.construction_year - item.construction_year)
                        score -= year_diff * 2
                    return score
                
                # Get top 3 similar vehicles
                similar_vehicles_sorted = sorted(similar_vehicles_with_prices, key=similarity_score, reverse=True)
                top_3_similar = similar_vehicles_sorted[:3]
                
                # Build context
                similar_context = ""
                if top_3_similar:
                    similar_context = "\n\nVÉHICULES SIMILAIRES DANS LA COLLECTION:"
                    for i, similar_vehicle in enumerate(top_3_similar, 1):
                        price = similar_vehicle.sold_price or similar_vehicle.current_value
                        status = "Vendu" if similar_vehicle.sold_price else "valeur actuelle"
                        similar_context += f"\n{i}. {similar_vehicle.name} ({similar_vehicle.construction_year or 'N/A'}) - {status}: {price:,.0f} CHF"
                        if similar_vehicle.description:
                            similar_context += f" - {similar_vehicle.description[:80]}..."
                
                # Create prompt for this vehicle
                prompt = f"""Estime le prix de marché actuel de ce véhicule en CHF :

VÉHICULE À ÉVALUER:
- Nom: {vehicle.name}
- Catégorie: {vehicle.category}
- Année: {vehicle.construction_year or 'N/A'}
- État: {vehicle.condition or 'N/A'}
- Description: {vehicle.description or 'N/A'}
{similar_context}

INSTRUCTIONS:
1. Utilise les prix actuels du marché pour ce modèle
2. Considère AutoScout24, Comparis et sites spécialisés
3. Prends en compte l'année, l'état et les spécificités

Réponds en JSON avec:
- estimated_price (nombre en CHF)
- reasoning (explication en français)
- confidence_score (0.1-0.9)
- market_trend (hausse/stable/baisse)"""
                
                # Get AI estimation
                market_analysis = ai_service.get_sophisticated_price_estimate(prompt)
                
                if 'error' not in market_analysis:
                    estimated_price = market_analysis.get('estimated_price')
                    if estimated_price and estimated_price > 0:
                        # Update vehicle with new price
                        update_data = {
                            'current_value': estimated_price,
                            'last_action_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        if db_manager.update_item(vehicle.id, update_data):
                            updated_count += 1
                            results.append({
                                'id': vehicle.id,
                                'name': vehicle.name,
                                'status': 'updated',
                                'new_price': estimated_price
                            })
                        else:
                            failed_count += 1
                            results.append({
                                'id': vehicle.id,
                                'name': vehicle.name,
                                'status': 'update_failed'
                            })
                    else:
                        failed_count += 1
                        results.append({
                            'id': vehicle.id,
                            'name': vehicle.name,
                            'status': 'invalid_price'
                        })
                else:
                    failed_count += 1
                    results.append({
                        'id': vehicle.id,
                        'name': vehicle.name,
                        'status': 'ai_error',
                        'error': market_analysis.get('error')
                    })
                    
            except Exception as e:
                logger.error(f"Error updating vehicle {vehicle.name}: {e}")
                failed_count += 1
                results.append({
                    'id': vehicle.id,
                    'name': vehicle.name,
                    'status': 'exception',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'Mise à jour terminée: {updated_count} succès, {failed_count} échecs',
            'updated': updated_count,
            'failed': failed_count,
            'total': len(vehicles),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error updating all vehicles: {e}")
        return jsonify({'error': 'Erreur lors de la mise à jour des véhicules'}), 500


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