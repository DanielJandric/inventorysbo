#!/usr/bin/env python3
"""
🚀 GPT-5 API Production - Déploiement Render
"""

import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vérification CRITIQUE de la clé API
if not os.getenv("OPENAI_API_KEY"):
    logger.error("🚨 ERREUR: OPENAI_API_KEY manquante!")
    raise ValueError("Variable OPENAI_API_KEY requise")

# Import après vérification
from gpt5_responses_final_with_helper import get_gpt5_response_final, GPT5ResponsesFinalManager

app = Flask(__name__)

@app.route("/api/gpt5/chat", methods=["POST"])
def gpt5_chat():
    """
    Endpoint principal pour le chat GPT-5
    Utilise l'API Responses avec fallback automatique
    """
    try:
        data = request.get_json()
        
        if not data or "message" not in data:
            return jsonify({
                "error": "Message requis",
                "success": False
            }), 400
        
        user_message = data["message"]
        system_prompt = data.get("system_prompt", "")
        context = data.get("context", "")
        
        logger.info(f"🤖 Demande de chat GPT-5: {user_message[:50]}...")
        
        # Appel GPT-5 avec fallback automatique
        result = get_gpt5_response_final(
            user_input=user_message,
            system_prompt=system_prompt,
            context=context,
            use_fallback=True  # Fallback automatique activé
        )
        
        if result["success"]:
            logger.info(f"✅ Réponse GPT-5 générée via {result['metadata']['method']}")
            return jsonify({
                "response": result["response"],
                "metadata": result["metadata"],
                "success": True
            })
        else:
            logger.error(f"❌ Échec GPT-5: {result['metadata'].get('error', 'Unknown')}")
            return jsonify({
                "error": "Impossible de générer une réponse",
                "details": result["metadata"],
                "success": False
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Erreur serveur: {e}")
        return jsonify({
            "error": "Erreur serveur interne",
            "success": False
        }), 500

@app.route("/api/gpt5/health", methods=["GET"])
def gpt5_health():
    """
    Vérification de santé du système GPT-5
    """
    try:
        from gpt5_responses_final_with_helper import GPT5ResponsesFinalManager
        
        manager = GPT5ResponsesFinalManager()
        health = manager.health_check()
        
        return jsonify({
            "status": "healthy" if health["overall_health"] else "degraded",
            "services": health,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "success": False
        }), 500

@app.route("/api/gpt5/test", methods=["POST"])
def gpt5_test():
    """
    Test simple de GPT-5
    """
    try:
        test_message = "Dis 'OK' en une phrase simple."
        
        result = get_gpt5_response_final(
            user_input=test_message,
            system_prompt="Tu es un assistant simple.",
            use_fallback=True
        )
        
        return jsonify({
            "test_message": test_message,
            "result": result,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route("/api/gpt5/context", methods=["GET"])
def gpt5_context():
    """
    Récupération du contexte de conversation actuel
    """
    try:
        from gpt5_responses_final_with_helper import GPT5ResponsesFinalManager
        
        manager = GPT5ResponsesFinalManager()
        context = manager.get_conversation_context()
        
        return jsonify({
            "context": context,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération contexte: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route("/api/gpt5/clear", methods=["POST"])
def gpt5_clear():
    """
    Effacement de l'historique de conversation
    """
    try:
        from gpt5_responses_final_with_helper import GPT5ResponsesFinalManager
        
        manager = GPT5ResponsesFinalManager()
        manager.clear_conversation_history()
        
        return jsonify({
            "message": "Historique de conversation effacé",
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur effacement: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route("/", methods=["GET"])
def home():
    """
    Page d'accueil avec documentation des endpoints
    """
    return """
    <h1>🚀 API GPT-5 Responses - Intégration Finale</h1>
    
    <h2>📋 Endpoints Disponibles</h2>
    
    <h3>🤖 Chat Principal</h3>
    <code>POST /api/gpt5/chat</code>
    <p>Envoie un message et reçoit une réponse GPT-5</p>
    <pre>
    {
        "message": "Votre question ici",
        "system_prompt": "Instructions système (optionnel)",
        "context": "Contexte additionnel (optionnel)"
    }
    </pre>
    
    <h3>🏥 Vérification de Santé</h3>
    <code>GET /api/gpt5/health</code>
    <p>Vérifie l'état des services GPT-5</p>
    
    <h3>🧪 Test Simple</h3>
    <code>POST /api/gpt5/test</code>
    <p>Teste le système avec un message simple</p>
    
    <h3>📚 Contexte de Conversation</h3>
    <code>GET /api/gpt5/context</code>
    <p>Récupère le contexte de conversation actuel</p>
    
    <h3>🗑️ Effacement</h3>
    <code>POST /api/gpt5/clear</code>
    <p>Efface l'historique de conversation</p>
    
    <h2>🔧 Fonctionnalités</h2>
    <ul>
        <li>✅ API Responses GPT-5 avec gestion automatique du contexte</li>
        <li>✅ Helper robuste d'extraction de texte</li>
        <li>✅ Fallback automatique vers Chat Completions</li>
        <li>✅ Gestion des erreurs et logging détaillé</li>
    </ul>
    
    <h2>📖 Utilisation</h2>
    <p>Envoyez une requête POST à <code>/api/gpt5/chat</code> avec votre message.</p>
    <p>Le système utilisera automatiquement l'API Responses et basculera vers Chat Completions si nécessaire.</p>
    """

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 Démarrage GPT-5 API sur le port {port}")
    logger.info(f"🔒 Mode debug: {debug}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
