#!/usr/bin/env python3
"""
Intégration Flask avec la solution GPT-5 FIXÉE
Utilise directement Chat Completions (qui fonctionne) au lieu de l'API Responses (défaillante)
"""

from flask import Flask, request, jsonify
from gpt5_chat_solution_fixed import get_gpt5_chat_response_fixed
import logging
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/api/markets/chat", methods=["POST"])
def markets_chat():
    """
    Chat de marché avec GPT-5 FIXÉ - Utilise directement Chat Completions
    Plus de drain de raisonnement de l'API Responses !
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
            # Note: J'ai commenté cette partie car supabase n'est pas importé
            # response = supabase.table('market_analyses').select('*').order('created_at', desc=True).limit(5).execute()
            
            # Pour le test, on utilise le contexte fourni par l'utilisateur
            context_text = extra_context if extra_context else ""
            
            # Simuler un contexte de base si nécessaire
            if not context_text:
                context_text = "Contexte: Analyse des marchés financiers actuels."
                
        except Exception as e:
            logger.warning(f"Erreur récupération contexte: {e}")
            context_text = f"Contexte additionnel (utilisateur):\n{extra_context}\n---\n" if extra_context else ""
        
        # Prompt système optimisé pour Chat Completions
        system_prompt = (
            "Tu es un analyste marchés expert. "
            "Utilise la mémoire de conversation si pertinent. "
            "Identifie les patterns (tendance, corrélations, régimes de volatilité) et commente risques/opportunités. "
            "N'invente jamais de chiffres. "
            "Si l'information manque, écris \"OK – Besoin de précisions : [liste courte]\". "
        )
        
        # Appel à la solution GPT-5 FIXÉE (Chat Completions direct)
        logger.info(f"🤖 Appel GPT-5 FIXÉ (Chat Completions) pour: {user_question[:50]}...")
        
        result = get_gpt5_chat_response_fixed(
            user_input=user_question,
            system_prompt=system_prompt,
            context=context_text,
            use_fallback=True  # Activer le fallback GPT-4 si nécessaire
        )
        
        if result['success']:
            # Succès - formater la réponse
            response_data = {
                "success": True,
                "reply": result['response'],
                "method": result['metadata']['method'],  # Pour debug/monitoring
                "metadata": {
                    "model_used": result['metadata'].get('model', 'unknown'),
                    "api_used": result['metadata'].get('api', 'unknown'),
                    "method": result['metadata'].get('method', 'unknown'),
                    "usage": result['metadata'].get('usage')
                }
            }
            
            # Log pour monitoring
            logger.info(f"✅ Chat GPT-5 FIXÉ réussi via {result['metadata']['method']}")
            
            return jsonify(response_data)
        
        else:
            # Échec - retourner le message de fallback
            logger.warning(f"⚠️ Chat GPT-5 FIXÉ échoué, utilisation du message de fallback")
            
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

# Endpoint pour vérifier la santé du système GPT-5 FIXÉ
@app.route("/api/gpt5/health", methods=["GET"])
def gpt5_health():
    """Vérification de santé du système GPT-5 FIXÉ"""
    try:
        from gpt5_chat_solution_fixed import GPT5ChatManagerFixed
        manager = GPT5ChatManagerFixed()
        health = manager.health_check()
        
        return jsonify({
            "success": True,
            "health": health,
            "status": "healthy" if health['overall_health'] else "degraded",
            "note": "Utilise Chat Completions (pas l'API Responses défaillante)"
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur health check GPT-5 FIXÉ: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "unhealthy"
        }), 500

# Endpoint de test simple
@app.route("/api/gpt5/test", methods=["POST"])
def gpt5_test():
    """Test simple de génération GPT-5"""
    try:
        data = request.get_json()
        test_prompt = data.get('prompt', 'Dis "OK" en une phrase.')
        
        result = get_gpt5_chat_response_fixed(
            user_input=test_prompt,
            system_prompt="Tu es un assistant de test.",
            use_fallback=False  # Test direct sans fallback
        )
        
        return jsonify({
            "success": result['success'],
            "response": result['response'],
            "metadata": result['metadata']
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur test GPT-5: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Route racine pour vérifier que l'API fonctionne
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "GPT-5 Chat API FIXÉE",
        "status": "running",
        "note": "Utilise Chat Completions au lieu de l'API Responses défaillante",
        "endpoints": {
            "chat": "/api/markets/chat",
            "health": "/api/gpt5/health",
            "test": "/api/gpt5/test"
        }
    })

if __name__ == "__main__":
    print("🚀 Démarrage de l'API GPT-5 FIXÉE")
    print("✅ Utilise Chat Completions (pas l'API Responses défaillante)")
    print("🔧 Plus de drain de raisonnement !")
    
    app.run(debug=True, port=5000)
