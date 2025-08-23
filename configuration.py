"""
Configuration et variables d'environnement pour l'application Inventory SBO
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Import configuration locale si disponible
try:
    import config as local_config
    logger.info("✅ Configuration locale chargée")
    
    # Utiliser les variables du fichier config.py local
    SUPABASE_URL = getattr(local_config, 'SUPABASE_URL', os.getenv("SUPABASE_URL"))
    SUPABASE_KEY = getattr(local_config, 'SUPABASE_KEY', os.getenv("SUPABASE_KEY"))
    OPENAI_API_KEY = getattr(local_config, 'OPENAI_API_KEY', os.getenv("OPENAI_API_KEY"))
    
    # Propager dans l'environnement pour les modules qui lisent os.getenv directement
    if SUPABASE_URL and not os.getenv("SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = str(SUPABASE_URL)
    if SUPABASE_KEY and not os.getenv("SUPABASE_KEY"):
        os.environ["SUPABASE_KEY"] = str(SUPABASE_KEY)
    if OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = str(OPENAI_API_KEY)
        
except ImportError:
    logger.info("⚠️ Fichier config.py non trouvé, utilisation des variables d'environnement")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Variables d'environnement principales
APP_URL = os.getenv("APP_URL", "https://inventorysbo.onrender.com")

# Variables d'environnement pour Gmail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")

# API Keys
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Configuration mise à jour automatique des prix (6x/jour)
AUTO_UPDATE_TIMES = [
    "09:00",  # Ouverture bourse suisse
    "11:00",  # Milieu matinée
    "13:00",  # Début après-midi
    "15:00",  # Milieu après-midi
    "17:00",  # Fermeture bourse suisse
    "21:30"   # Soirée (après les marchés US)
]

# Configuration Market Updates
MARKET_UPDATE_TIME = "21:30"  # Heure de génération automatique
MARKET_UPDATE_TIMEZONE = "Europe/Paris"  # Timezone pour les updates

# Configuration API Manus pour rapports financiers
MANUS_API_BASE_URL = "https://e5h6i7cn86z0.manus.space"

# Configuration FreeCurrency (pour conversion USD/EUR vers CHF)
FREECURRENCY_API_KEY = os.getenv("FREECURRENCY_API_KEY", "fca_live_MhoTdTd6auvKD1Dr5kVQ7ua9SwgGPApjylr3CrRe")

# Cache pour les taux de change avec expiration
FOREX_CACHE_DURATION = 3600  # 1 heure

# Validation des variables critiques
def validate_environment():
    """Valide que les variables critiques sont définies"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Variables d'environnement manquantes")
        logger.error(f"SUPABASE_URL: {'✅' if SUPABASE_URL else '❌'}")
        logger.error(f"SUPABASE_KEY: {'✅' if SUPABASE_KEY else '❌'}")
        raise EnvironmentError("SUPABASE_URL et SUPABASE_KEY sont requis")
    
    logger.info("Variables d'environnement validées")
    
    return {
        'supabase_configured': bool(SUPABASE_URL and SUPABASE_KEY),
        'openai_configured': bool(OPENAI_API_KEY),
        'email_configured': bool(EMAIL_USER and EMAIL_PASSWORD),
        'finnhub_configured': bool(FINNHUB_API_KEY),
    }
