"""
Configuration module for the Inventory SBO application.
Centralizes all configuration settings and environment variables.
"""

import os
import logging
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Central configuration class"""
    
    # Application settings
    APP_URL = os.getenv("APP_URL", "https://inventorysbo.onrender.com")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Database configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Email configuration
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")
    
    # Stock API configurations
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    FREECURRENCY_API_KEY = os.getenv("FREECURRENCY_API_KEY", "fca_live_MhoTdTd6auvKD1Dr5kVQ7ua9SwgGPApjylr3CrRe")
    
    # Manus API configuration
    MANUS_API_BASE_URL = "https://e5h6i7cn86z0.manus.space"
    
    # Google APIs configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
    
    # ScrapingBee configuration
    SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")
    
    # Auto-update configuration
    AUTO_UPDATE_TIMES = [
        "09:00",  # Ouverture bourse suisse
        "11:00",  # Milieu matinée
        "13:00",  # Début après-midi
        "15:00",  # Milieu après-midi
        "17:00",  # Fermeture bourse suisse
        "21:30"   # Soirée (après les marchés US)
    ]
    
    # Market update configuration
    MARKET_UPDATE_TIME = "21:30"
    MARKET_UPDATE_TIMEZONE = "Europe/Paris"
    
    # Cache configuration
    FOREX_CACHE_DURATION = 3600  # 1 hour
    STOCK_PRICE_CACHE_DURATION = 300  # 5 minutes
    
    # Rate limiting
    MAX_DAILY_REQUESTS = 500
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing = []
        
        for key in required:
            if not getattr(cls, key):
                missing.append(key)
        
        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            return False
        
        logger.info("Configuration validated successfully")
        return True
    
    @classmethod
    def load_local_config(cls):
        """Try to load configuration from local config.py file"""
        try:
            import config as local_config
            logger.info("✅ Local configuration loaded")
            
            # Override with local config values
            for attr in dir(local_config):
                if not attr.startswith('_'):
                    value = getattr(local_config, attr, None)
                    if value is not None:
                        setattr(cls, attr, value)
                        # Also set in environment for modules that read os.getenv directly
                        if isinstance(value, str):
                            os.environ[attr] = value
        except ImportError:
            logger.info("⚠️ Local config.py not found, using environment variables")


# Initialize configuration
Config.load_local_config()

# Export commonly used values
SUPABASE_URL = Config.SUPABASE_URL
SUPABASE_KEY = Config.SUPABASE_KEY
OPENAI_API_KEY = Config.OPENAI_API_KEY