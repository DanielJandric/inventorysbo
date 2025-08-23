#!/usr/bin/env python3
"""
Exemple d'intégration de la solution GPT-5 robuste dans votre app Flask
Remplace la section chat de app.py avec un fallback qui fonctionne
"""

from flask import jsonify, request
from gpt5_chat_solution import get_gpt5_chat_response
import logging

logger = logging.getLogger(__name__)

@app.route("/api/markets/chat", methods=["POST"])
def markets_chat():
    """
    Chat de marché avec GPT-5 robuste
    Utilise la stratégie de fallback qui fonctionne pour vos rapports
    """
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        extra_context = data.get('context', '')
        
        if not user_question:
            return jsonify({"success": False, "error": "Question requise"}), 400
        
        # Construire le contexte depuis la base de données (votre logique existante)
        context_text = ""
        try:
            # Votre logique existante pour récupérer le contexte depuis Supabase
            response = supabase.table('market_analyses').select('*').order('created_at', desc=True).limit(5).execute()
            
            context_parts = []
            for item in response.data:
                try:
                    analysis_data = json.loads(item.get('analysis_data', '{}'))
                    if analysis_data.get('summary'):
                        context_parts.append(
                            f"• {item.get('created_at', 'N/A')} : {analysis_data['summary'][:200]}..."
                        )
                except Exception:
                    continue
            
            context_text = "\n".join(context_parts)
            if extra_context:
                context_text = f"Contexte additionnel (utilisateur):\n{extra_context}\n---\n" + context_text
                
            # Limiter la taille du contexte
            if len(context_text) > 2000:
                context_text = context_text[:2000]
                
        except Exception as e:
            logger.warning(f"Erreur récupération contexte: {e}")
            context_text = f"Contexte additionnel (utilisateur):\n{extra_context}\n---\n" if extra_context else ""
        
        # Prompt système optimisé
        system_prompt = (
            "Tu es un analyste marchés expert. "
            "Utilise la mémoire de conversation si pertinent. "
            "Identifie les patterns (tendance, corrélations, régimes de volatilité) et commente risques/opportunités. "
            "N'invente jamais de chiffres. "
            "Si l'information manque, écris \"OK – Besoin de précisions : [liste courte]\". "
        )
        
        # Appel à la solution robuste GPT-5
        logger.info(f"🤖 Appel GPT-5 robuste pour: {user_question[:50]}...")
        
        result = get_gpt5_chat_response(
            user_input=user_question,
            system_prompt=system_prompt,
            context=context_text
        )
        
        if result['success']:
            # Succès - formater la réponse
            response_data = {
                "success": True,
                "reply": result['response'],
                "method": result['method'],  # Pour debug/monitoring
                "metadata": {
                    "model_used": result['metadata'].get('model', 'unknown'),
                    "api_used": result['metadata'].get('api', 'unknown'),
                    "request_id": result['metadata'].get('request_id'),
                    "usage": result['metadata'].get('usage')
                }
            }
            
            # Log pour monitoring
            logger.info(f"✅ Chat GPT-5 réussi via {result['method']}")
            
            return jsonify(response_data)
        
        else:
            # Échec - retourner le message de fallback
            logger.warning(f"⚠️ Chat GPT-5 échoué, utilisation du message de fallback")
            
            return jsonify({
                "success": False,
                "error": "Service temporairement indisponible",
                "fallback_message": result['response']
            }), 500
    
    except Exception as e:
        logger.error(f"❌ Erreur chat markets: {e}")
        return jsonify({
            "success": False,
            "error": "Erreur interne du serveur",
            "fallback_message": "OK – Besoin de précisions : le service est temporairement indisponible. Veuillez réessayer."
        }), 500

# Endpoint pour vérifier la santé du système GPT-5
@app.route("/api/gpt5/health", methods=["GET"])
def gpt5_health():
    """Vérification de santé du système GPT-5"""
    try:
        from gpt5_chat_solution import GPT5ChatManager
        manager = GPT5ChatManager()
        health = manager.health_check()
        
        return jsonify({
            "success": True,
            "health": health,
            "status": "healthy" if health['overall_health'] else "degraded"
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur health check GPT-5: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "unhealthy"
        }), 500
