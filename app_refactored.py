"""
Application Flask principale - Version refactorisée
"""
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# Import des modules refactorisés
from configuration import validate_environment, SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY
from managers import SmartCache, ConversationMemoryStore, GmailNotificationManager
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

# Initialisation des managers globaux
smart_cache = SmartCache()
conversation_memory = ConversationMemoryStore()
gmail_manager = GmailNotificationManager()

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
