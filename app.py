"""
Application Flask principale - Version refactorisée
"""
import logging
from datetime import datetime
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

if __name__ == "__main__":
    logger.info("🚀 Démarrage de l'application refactorisée")
    app.run(debug=True, host='0.0.0.0', port=5000)
