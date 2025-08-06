#!/usr/bin/env python3
"""
Configuration du Background Worker
"""

# Configuration des intervalles (en heures)
INTERVALS = {
    'market_analysis': 4,      # Analyse de marché toutes les 4 heures
    'error_retry': 1,          # Retry en cas d'erreur après 1 heure
    'health_check': 0.5        # Vérification de santé toutes les 30 minutes
}

# Configuration des prompts
PROMPTS = {
    'market_analysis': "Résume moi parfaitement et d'une façon exhaustive la situation sur les marchés financiers aujourd'hui. Aussi, je veux un focus particulier sur l'IA. Inclus les indices majeurs, les tendances, les actualités importantes, et les développements technologiques.",
    'ai_focus': "Analyse approfondie des développements en intelligence artificielle dans les marchés financiers, incluant les nouvelles technologies, les investissements, et les impacts sur les secteurs traditionnels.",
    'crypto_analysis': "Analyse complète du marché des cryptomonnaies, incluant Bitcoin, Ethereum, et les tendances DeFi et NFT."
}

# Configuration du scraping
SCRAPING_CONFIG = {
    'num_sources': 3,          # Nombre de sources à scraper
    'max_content_length': 8000, # Longueur maximale du contenu
    'timeout_seconds': 300     # Timeout pour chaque requête (5 minutes)
}

# Configuration du logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': None,  # Pas de fichier de log sur Render
    'console': True
}

# Configuration des variables d'environnement requises
REQUIRED_ENV_VARS = [
    'SCRAPINGBEE_API_KEY',
    'OPENAI_API_KEY'
]

# Configuration des sites financiers
FINANCIAL_SITES = {
    'general_markets': [
        'https://www.reuters.com/markets/',
        'https://www.bloomberg.com/markets',
        'https://www.ft.com/markets',
        'https://www.cnbc.com/markets/',
        'https://www.marketwatch.com/'
    ],
    'ai_tech': [
        'https://techcrunch.com/tag/artificial-intelligence/',
        'https://www.theverge.com/ai-artificial-intelligence',
        'https://www.wired.com/tag/artificial-intelligence/',
        'https://www.technologyreview.com/topic/artificial-intelligence/'
    ]
} 