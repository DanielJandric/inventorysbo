"""
Application Flask principale - Version refactorisée
"""
import logging
import uuid
import json
import re
import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request, make_response
from flask_cors import CORS

# Import des modules refactorisés
from configuration import validate_environment, SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY
from managers import smart_cache, conversation_memory, gmail_manager
from models import CollectionItem, QueryIntent
from routes_markets import markets_bp, init_markets_routes

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validation des variables d'environnement
try:
    env_status = validate_environment()
    logger.info(f"✅ Configuration validée: {env_status}")
except EnvironmentError as e:
    logger.error(f"❌ Erreur configuration: {e}")
    raise

# Les managers globaux sont importés de managers.py

# Initialisation des clients et connexions
supabase = None
openai_client = None

try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase connecté")
except Exception as e:
    logger.error(f"❌ Erreur Supabase: {e}")
    raise

try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI connecté")
    else:
        logger.warning("⚠️ OpenAI non configuré")
except Exception as e:
    logger.warning(f"⚠️ OpenAI non disponible: {e}")

# Initialisation des managers dépendants
web_search_manager = None
if openai_client:
    try:
        from web_search_manager import create_web_search_manager
        web_search_manager = create_web_search_manager(openai_client)
        logger.info("✅ Gestionnaire de recherche web initialisé")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation Web Search Manager: {e}")

# Initialisation Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Session-Id"]
    }
})

# Enregistrement des blueprints
init_markets_routes(openai_client, web_search_manager)
app.register_blueprint(markets_bp)

# Enregistrement du blueprint metrics
try:
    from metrics_api import metrics_bp as metrics_blueprint
    app.register_blueprint(metrics_blueprint, url_prefix='/api/metrics')
    logger.info("✅ Metrics blueprint enregistré")
except Exception as e:
    logger.error(f"❌ Erreur enregistrement metrics: {e}")

# Routes principales de base
@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

# ===== ROUTES API COLLECTION (CRITIQUES) =====

@app.route("/api/items", methods=["GET"])
def get_items():
    """Récupérer tous les items de la collection"""
    try:
        query = supabase.table("items").select("*").order('created_at', desc=True)
        response = query.execute()
        return jsonify(response.data)
    except Exception as e:
        logger.error(f"Erreur get_items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items", methods=["POST"])
def add_item():
    """Ajouter un nouvel item à la collection"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Aucune donnée fournie"}), 400

        # Validation des champs requis
        required_fields = ['name', 'category', 'current_value']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Champ requis manquant: {field}"}), 400

        # Conversion du prix
        try:
            data['current_value'] = float(data['current_value'])
        except (ValueError, TypeError):
            return jsonify({"error": "current_value doit être un nombre"}), 400

        # Insertion dans Supabase
        response = supabase.table("items").insert(data).execute()
        
        if response.data:
            logger.info(f"✅ Item ajouté: {data['name']}")
            return jsonify({"success": True, "data": response.data[0]})
        else:
            return jsonify({"error": "Échec de l'ajout"}), 500
            
    except Exception as e:
        logger.error(f"Erreur add_item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Mettre à jour un item existant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Aucune donnée fournie"}), 400

        # Conversion du prix si présent
        if 'current_value' in data:
            try:
                data['current_value'] = float(data['current_value'])
            except (ValueError, TypeError):
                return jsonify({"error": "current_value doit être un nombre"}), 400

        # Mise à jour
        response = supabase.table("items").update(data).eq('id', item_id).execute()
        
        if response.data:
            logger.info(f"✅ Item {item_id} mis à jour")
            return jsonify({"success": True, "data": response.data[0]})
        else:
            return jsonify({"error": "Item non trouvé"}), 404
            
    except Exception as e:
        logger.error(f"Erreur update_item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Supprimer un item de la collection"""
    try:
        response = supabase.table("items").delete().eq('id', item_id).execute()
        
        if response.data:
            logger.info(f"✅ Item {item_id} supprimé")
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Item non trouvé"}), 404
            
    except Exception as e:
        logger.error(f"Erreur delete_item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/analytics/advanced")
def advanced_analytics():
    """Analytics avancés de la collection"""
    try:
        # Récupérer tous les items
        response = supabase.table("items").select("*").execute()
        items = response.data or []

        if not items:
            return jsonify({
                "total_items": 0,
                "total_value": 0,
                "asset_classes": {},
                "top_items": []
            })

        # Calculs analytics
        total_value = sum(float(item.get('current_value', 0)) for item in items)
        total_items = len(items)

        # Répartition par catégories
        asset_classes = {}
        for item in items:
            category = item.get('category', 'Unknown')
            value = float(item.get('current_value', 0))
            
            if category not in asset_classes:
                asset_classes[category] = {"count": 0, "value": 0}
            
            asset_classes[category]["count"] += 1
            asset_classes[category]["value"] += value

        # Top 10 items par valeur
        top_items = sorted(items, key=lambda x: float(x.get('current_value', 0)), reverse=True)[:10]

        return jsonify({
            "total_items": total_items,
            "total_value": total_value,
            "asset_classes": asset_classes,
            "top_items": top_items
        })

    except Exception as e:
        logger.error(f"Erreur advanced_analytics: {e}")
        return jsonify({"error": str(e)}), 500

# ===== ROUTES API STOCK ET PRIX =====

@app.route("/api/stock-price/<symbol>")
def get_stock_price(symbol):
    """Obtenir le prix d'une action"""
    try:
        from stock_api_manager import get_stock_price_stable
        price_data = get_stock_price_stable(symbol)
        return jsonify(price_data)
    except Exception as e:
        logger.error(f"Erreur stock_price {symbol}: {e}")
        return jsonify({"error": str(e), "symbol": symbol}), 500

@app.route("/api/exchange-rate/<from_currency>/<to_currency>")
def get_exchange_rate(from_currency, to_currency):
    """Obtenir un taux de change"""
    try:
        from manus_integration import get_exchange_rate_manus
        rate = get_exchange_rate_manus(from_currency, to_currency)
        return jsonify({
            "from": from_currency,
            "to": to_currency,
            "rate": rate,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur exchange_rate {from_currency}/{to_currency}: {e}")
        return jsonify({"error": str(e)}), 500

# ===== ROUTES API RAPPORTS =====

@app.route("/api/portfolio/pdf", methods=["GET"])
def generate_portfolio_pdf():
    """Générer un PDF du portfolio"""
    try:
        # Récupérer les données de la collection
        response = supabase.table("items").select("*").order('current_value', desc=True).execute()
        items = response.data or []
        
        if not items:
            return jsonify({"error": "Aucun item dans la collection"}), 404

        # Import du générateur PDF
        from pdf_optimizer import generate_optimized_pdf
        
        # Générer le PDF
        pdf_content = generate_optimized_pdf(items)
        
        # Créer la réponse
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="portfolio_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur portfolio_pdf: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analytics')
def analytics():
    """Page analytics"""
    return render_template('analytics.html')

@app.route('/sold')
def sold():
    """Page des objets vendus"""
    return render_template('sold.html')

@app.route('/reports')
def reports():
    """Page des rapports"""
    return render_template('reports.html')

@app.route('/settings')
def settings():
    """Page des paramètres et configuration"""
    return render_template('settings.html')

@app.route('/real-estate')
def real_estate():
    """Page immobilier"""
    return render_template('real_estate.html')

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "supabase": bool(supabase),
            "openai": bool(openai_client),
            "web_search": bool(web_search_manager),
        }
    })

# ===== ROUTES API ANALYSES DE MARCHÉ =====

@app.route("/api/market-analyses/recent", methods=["GET"])
def get_recent_market_analyses():
    """Retourne les 15 dernières analyses pour affichage dans la page marchés."""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        items = db.get_recent_analyses(limit=15)
        return jsonify({
            "success": True,
            "items": [a.to_frontend_dict() for a in items]
        })
    except Exception as e:
        logger.error(f"Erreur get_recent_market_analyses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/market-analyses/<int:analysis_id>", methods=["DELETE"])
def delete_market_analysis(analysis_id):
    """Supprimer une analyse de marché"""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        success = db.delete_analysis(analysis_id)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Analyse non trouvée"}), 404
            
    except Exception as e:
        logger.error(f"Erreur delete_market_analysis: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/market-updates", methods=["GET"])
def get_market_updates():
    """Récupère tous les briefings de marché"""
    try:
        if not supabase:
            return jsonify({"error": "Supabase non connecté"}), 500
        
        response = supabase.table("market_updates").select("*").order("created_at", desc=True).limit(10).execute()
        
        if response.data:
            return jsonify({
                "success": True,
                "updates": response.data
            })
        else:
            return jsonify({
                "success": True,
                "updates": [],
                "message": "Aucun briefing trouvé"
            })
            
    except Exception as e:
        logger.error(f"Erreur get_market_updates: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/market-pdfs", methods=["GET"])
def list_market_pdfs():
    """Liste les PDFs déposés pour les updates de marché."""
    try:
        import os
        
        # Chercher dans différents dossiers possibles
        possible_folders = [
            "static/market_pdfs",
            "market_pdfs", 
            "uploads/market_pdfs"
        ]
        
        folder_path = None
        for folder in possible_folders:
            if os.path.exists(folder):
                folder_path = folder
                break
        
        if not folder_path:
            # Créer le dossier s'il n'existe pas
            folder_path = "static/market_pdfs"
            os.makedirs(folder_path, exist_ok=True)
        
        files = []
        try:
            for entry in os.scandir(folder_path):
                if entry.is_file() and entry.name.lower().endswith('.pdf'):
                    stat = entry.stat()
                    files.append({
                        "name": entry.name,
                        "url": f"/static/market_pdfs/{entry.name}",
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        except OSError:
            pass  # Dossier vide ou inaccessible
        
        # Les plus récents d'abord
        files.sort(key=lambda x: x["modified_at"], reverse=True)
        
        return jsonify({
            "success": True,
            "files": files,
            "folder": folder_path
        })
        
    except Exception as e:
        logger.error(f"Erreur list_market_pdfs: {e}")
        return jsonify({"success": False, "error": str(e), "files": []}), 500

# ===== ROUTES IA CRITIQUES =====

@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    """Chatbot utilisant OpenAI GPT-4 avec recherche sémantique RAG et mémoire conversationnelle"""
    try:
        if not openai_client:
            return jsonify({"error": "Moteur IA indisponible"}), 503
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données requises"}), 400
        
        query = data.get("message", "").strip()
        if not query:
            return jsonify({"error": "Message requis"}), 400
        
        # Session et historique
        session_id = data.get("session_id") or request.headers.get("X-Session-Id") or str(uuid.uuid4())
        session_id = session_id.strip()
        
        history_client = data.get("history", [])
        history_persisted = conversation_memory.get_recent_messages(session_id, limit=12)
        
        # Fusion: mémoire persistée + derniers messages du client
        conversation_history = (history_persisted or []) + (list(history_client[-8:]) if isinstance(history_client, list) else [])
        
        logger.info(f"🎯 Requête chatbot: '{query}' avec {len(conversation_history)} messages d'historique")
        
        # Récupérer les items de la collection pour le contexte
        try:
            items_response = supabase.table("items").select("*").execute()
            items = items_response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération items: {e}")
            items = []
        
        # Construire le contexte de la collection
        collection_context = ""
        if items:
            total_value = sum(float(item.get('current_value', 0)) for item in items)
            categories = {}
            for item in items:
                cat = item.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            collection_context = f"""
CONTEXTE COLLECTION BONVIN:
- Total items: {len(items)}
- Valeur totale: {total_value:,.0f} CHF
- Catégories: {', '.join(f"{cat} ({count})" for cat, count in categories.items())}

DERNIERS ITEMS:
"""
            for item in items[:5]:  # Top 5 items par valeur
                collection_context += f"- {item.get('name', 'N/A')} ({item.get('category', 'N/A')}) - {item.get('current_value', 0):,.0f} CHF\n"
        
        # Messages pour l'IA avec contexte
        messages = [
            {"role": "system", "content": f"""Tu es l'assistant IA de BONVIN Collection, une collection privée d'objets de luxe et d'investissements.

RÔLE: Aide avec les questions sur la collection, l'évaluation d'objets, les investissements et les marchés financiers.

{collection_context}

INSTRUCTIONS:
- Sois précis et informatif
- Utilise les données de la collection quand pertinent
- Aide avec l'évaluation, l'analyse et les conseils d'investissement
- Si on te demande d'ajouter un objet, explique que tu peux analyser mais pas modifier la base directement"""}
        ]
        
        # Ajouter l'historique de conversation
        for msg in conversation_history[-10:]:  # Limiter à 10 derniers messages
            if isinstance(msg, dict) and msg.get('role') in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Ajouter le message actuel
        messages.append({"role": "user", "content": query})
        
        # Appeler l'IA
        response = openai_client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4-turbo-preview"),
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            timeout=30
        )
        
        reply = response.choices[0].message.content.strip()
        
        # Sauvegarder dans la mémoire conversationnelle
        try:
            conversation_memory.add_message(session_id, 'user', query)
            conversation_memory.add_message(session_id, 'assistant', reply)
        except Exception as e:
            logger.error(f"Erreur sauvegarde conversation: {e}")
        
        return jsonify({
            "reply": reply,
            "metadata": {
                "session_id": session_id,
                "mode": "chatbot_rag",
                "model": os.getenv("AI_MODEL", "gpt-4-turbo-preview"),
                "items_count": len(items),
                "conversation_length": len(conversation_history)
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur chatbot: {e}")
        return jsonify({"error": f"Erreur chatbot: {str(e)}"}), 500

@app.route("/api/ai-update-price/<int:item_id>", methods=["POST"])
def ai_update_price(item_id):
    """Mise à jour automatique du prix via IA et sauvegarde en base"""
    if not openai_client:
        return jsonify({"error": "Moteur IA Indisponible"}), 503
    
    try:
        # Récupérer l'item cible
        response = supabase.table("items").select("*").eq("id", item_id).execute()
        if not response.data:
            return jsonify({"error": "Objet non trouvé"}), 404
        
        target_item = response.data[0]
        
        # Vérifier que c'est pas une action
        if target_item.get('category') == 'Actions':
            return jsonify({"error": "Cette fonction est réservée aux véhicules. Utilisez la mise à jour des prix d'actions pour les actions."}), 400
        
        # Récupérer tous les items pour comparaison
        all_items_response = supabase.table("items").select("*").execute()
        all_items = all_items_response.data or []
        
        # Trouver des objets similaires
        similar_items = [
            i for i in all_items 
            if i.get('category') == target_item.get('category') 
            and i.get('id') != item_id
            and (i.get('current_value') or i.get('sold_price'))
        ]
        
        # Contexte des objets similaires
        similar_context = ""
        if similar_items[:3]:  # Top 3
            similar_context = "\n\nOBJETS SIMILAIRES DANS LA COLLECTION:"
            for i, similar_item in enumerate(similar_items[:3], 1):
                price = similar_item.get('sold_price') or similar_item.get('current_value')
                status = "Vendu" if similar_item.get('sold_price') else "valeur actuelle"
                similar_context += f"\n{i}. {similar_item.get('name')} ({similar_item.get('construction_year') or 'N/A'}) - {status}: {price:,.0f} CHF"
                if similar_item.get('description'):
                    similar_context += f" - {similar_item['description'][:80]}..."
        
        # Prompt JSON structuré
        prompt = f"""Estime le prix de marché actuel de cet objet en CHF en te basant sur le marché réel :

OBJET À ÉVALUER:
- Nom: {target_item.get('name', 'N/A')}
- Catégorie: {target_item.get('category', 'N/A')}
- Année: {target_item.get('construction_year', 'N/A')}
- État: {target_item.get('condition', 'N/A')}
- Description: {target_item.get('description', 'N/A')}
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

        # Utiliser l'API GPT-4 avec format JSON
        from gpt5_compat import from_responses_simple, extract_output_text
        
        response = from_responses_simple(
            client=openai_client, 
            model=os.getenv("AI_MODEL", "gpt-4-turbo-preview"),
            messages=[
                {"role": "system", "content": [{"type": "input_text", "text": "Tu es un expert en évaluation d'objets de luxe et d'actifs financiers avec une connaissance approfondie du marché. Réponds en JSON."}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]}
            ],
            max_output_tokens=800,
            timeout=20,
            reasoning_effort="medium"
        )
        
        raw = extract_output_text(response) or ''
        
        # Parsing robuste JSON
        def _safe_parse_json(text: str):
            s = (text or '').strip()
            try:
                import re
                s = re.sub(r"```\s*json\s*", "", s, flags=re.IGNORECASE)
                s = s.replace('```', '').strip()
                # Normaliser les quotes
                trans = {ord('\u201c'): '"', ord('\u201d'): '"', ord('\u2019'): "'", ord('\u2013'): '-', ord('\u2014'): '-'}
                s = s.translate(trans)
                return json.loads(s)
            except Exception as e:
                logger.error(f"JSON parse error: {e}, text: {s[:200]}")
                return None
        
        parsed = _safe_parse_json(raw)
        if not parsed:
            return jsonify({"error": f"L'IA n'a pas renvoyé un JSON valide. Réponse brute: {raw[:200]}..."}), 400
        
        estimated_price = parsed.get('estimated_price')
        if not isinstance(estimated_price, (int, float)) or estimated_price <= 0:
            return jsonify({"error": f"Prix estimé invalide: {estimated_price}"}), 400
        
        # Mettre à jour en base
        update_response = supabase.table("items").update({
            "current_value": float(estimated_price)
        }).eq("id", item_id).execute()
        
        if not update_response.data:
            return jsonify({"error": "Échec mise à jour base de données"}), 500
        
        return jsonify({
            "success": True,
            "item_id": item_id,
            "estimated_price": float(estimated_price),
            "previous_price": target_item.get('current_value'),
            "reasoning": parsed.get('reasoning', 'N/A'),
            "confidence_score": parsed.get('confidence_score', 0.5),
            "market_trend": parsed.get('market_trend', 'stable'),
            "ai_response": raw[:200] + "..." if len(raw) > 200 else raw
        })
        
    except Exception as e:
        logger.error(f"Erreur ai_update_price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/background-worker/trigger", methods=["POST"])
def trigger_background_worker():
    """Déclencher le worker d'analyse de marché"""
    try:
        from market_analysis_db import get_market_analysis_db, MarketAnalysis

        db = get_market_analysis_db()
        
        # Récupérer le prompt du corps de la requête
        request_data = request.get_json(silent=True) or {}
        prompt = request_data.get('prompt', "Analyse exhaustive des marchés financiers aujourd'hui avec focus IA")
        
        # Créer une nouvelle analyse
        analysis = MarketAnalysis(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_type='background_worker',
            prompt=prompt,
            summary="Analyse en cours...",
            key_points=["Analyse lancée par le worker"]
        )
        
        analysis_id = db.save_analysis(analysis)
        
        # Simuler le démarrage du worker (en réalité cela devrait être async)
        logger.info(f"✅ Worker analysis {analysis_id} créée avec prompt: {prompt[:50]}...")
        
        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "message": "Worker d'analyse lancé",
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
        })
        
    except Exception as e:
        logger.error(f"Erreur trigger_background_worker: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/background-worker/status", methods=["GET"])
def background_worker_status():
    """Statut du background worker"""
    try:
        from market_analysis_db import get_market_analysis_db
        
        db = get_market_analysis_db()
        latest_analysis = db.get_latest_analysis()
        
        if latest_analysis:
            return jsonify({
                "success": True,
                "status": "available",
                "latest_analysis": {
                    "id": latest_analysis.id,
                    "timestamp": latest_analysis.timestamp,
                    "type": latest_analysis.analysis_type,
                    "summary": latest_analysis.summary[:100] + "..." if latest_analysis.summary and len(latest_analysis.summary) > 100 else latest_analysis.summary
                }
            })
        else:
            return jsonify({
                "success": True,
                "status": "no_analysis",
                "message": "Aucune analyse trouvée"
            })
            
    except Exception as e:
        logger.error(f"Erreur background_worker_status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'application refactorisée")
    app.run(debug=True, host='0.0.0.0', port=5000)
