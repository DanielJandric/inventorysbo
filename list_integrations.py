#!/usr/bin/env python3
"""
Script pour lister et afficher toutes les intégrations disponibles
"""

import os
import json
from datetime import datetime

def print_header():
    """Affiche l'en-tête du script"""
    print("=" * 80)
    print("🔗 SYSTÈME D'INFORMATIONS FINANCIÈRES - VUE D'ENSEMBLE DES INTÉGRATIONS")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_file_exists(filename):
    """Vérifie si un fichier existe"""
    return os.path.exists(filename)

def get_file_size(filename):
    """Obtient la taille d'un fichier"""
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size // 1024} KB"
        else:
            return f"{size // (1024 * 1024)} MB"
    return "N/A"

def list_search_integrations():
    """Liste les intégrations de recherche"""
    print("🔍 INTÉGRATIONS DE RECHERCHE WEB & IA")
    print("-" * 50)
    
    integrations = [
        {
            "name": "OpenAI Web Search",
            "file": "web_search_manager.py",
            "docs": ["WEB_SEARCH_IMPLEMENTATION.md", "WEB_SEARCH_SUMMARY.md"],
            "tests": ["test_web_search_integration.py"],
            "interface": "/web-search",
            "endpoints": [
                "POST /api/web-search/market-briefing",
                "POST /api/web-search/financial-markets", 
                "GET /api/web-search/stock/<symbol>",
                "GET /api/web-search/market-alerts",
                "GET /api/web-search/status"
            ]
        },
        {
            "name": "Google Search API",
            "file": "google_search_manager.py",
            "docs": ["GOOGLE_SEARCH_IMPLEMENTATION.md", "GOOGLE_SEARCH_SUMMARY.md"],
            "tests": ["test_google_search_integration.py"],
            "interface": "/google-search",
            "endpoints": [
                "POST /api/google-search/market-report",
                "POST /api/google-search/daily-news",
                "POST /api/google-search/financial-markets",
                "GET /api/google-search/stock/<symbol>",
                "GET /api/google-search/status"
            ]
        }
    ]
    
    for integration in integrations:
        print(f"\n📊 {integration['name']}")
        print(f"   📁 Module: {integration['file']} ({get_file_size(integration['file'])})")
        print(f"   🌐 Interface: http://localhost:5000{integration['interface']}")
        
        # Vérifier les fichiers
        status = "✅" if check_file_exists(integration['file']) else "❌"
        print(f"   {status} Module principal")
        
        for doc in integration['docs']:
            status = "✅" if check_file_exists(doc) else "❌"
            print(f"   {status} Documentation: {doc}")
        
        for test in integration['tests']:
            status = "✅" if check_file_exists(test) else "❌"
            print(f"   {status} Tests: {test}")
        
        print("   🔗 Endpoints:")
        for endpoint in integration['endpoints']:
            print(f"      - {endpoint}")

def list_stock_integrations():
    """Liste les intégrations boursières"""
    print("\n📈 INTÉGRATIONS BOURSIÈRES")
    print("-" * 50)
    
    integrations = [
        {
            "name": "Manus API",
            "files": ["manus_integration.py", "stable_manus_wrapper.py", "manus_flask_integration.py"],
            "tests": ["test_manus_integration.py", "test_manus_detailed_analysis.py"],
            "endpoints": [
                "GET /api/market-report/manus",
                "GET /api/market-updates",
                "POST /api/market-updates/trigger"
            ]
        },
        {
            "name": "Yahoo Finance",
            "files": ["yahoo_finance_api.py", "yahoo_finance_auth.py", "yahoo_fallback.py"],
            "tests": ["test_yahoo_finance.py", "test_yahoo_auth.py", "test_yfinance_integration.py"],
            "endpoints": [
                "GET /api/stock-price/<symbol>",
                "GET /api/stock-price/history/<symbol>",
                "POST /api/stock-price/update-all"
            ]
        },
        {
            "name": "Alpha Vantage",
            "files": ["alpha_vantage_fallback.py"],
            "tests": ["test_alpha_vantage.py", "test_alpha_vantage_with_key.py"],
            "endpoints": [
                "GET /api/stock-price/<symbol> (fallback)"
            ]
        }
    ]
    
    for integration in integrations:
        print(f"\n📊 {integration['name']}")
        
        for file in integration['files']:
            status = "✅" if check_file_exists(file) else "❌"
            print(f"   {status} {file} ({get_file_size(file)})")
        
        for test in integration['tests']:
            status = "✅" if check_file_exists(test) else "❌"
            print(f"   {status} Test: {test}")
        
        print("   🔗 Endpoints:")
        for endpoint in integration['endpoints']:
            print(f"      - {endpoint}")

def list_other_integrations():
    """Liste les autres intégrations"""
    print("\n🛠️ AUTRES INTÉGRATIONS")
    print("-" * 50)
    
    integrations = [
        {
            "name": "FreeCurrency API",
            "description": "Conversion de devises",
            "endpoint": "GET /api/exchange-rate/<from_currency>/<to_currency>",
            "config": "FREECURRENCY_API_KEY"
        },
        {
            "name": "OpenAI Chat",
            "description": "Chatbot intelligent",
            "endpoint": "POST /api/chatbot",
            "features": ["Analyse sémantique", "RAG", "Réponses contextuelles"]
        },
        {
            "name": "Embeddings",
            "description": "Recherche sémantique",
            "endpoints": [
                "GET /api/embeddings/status",
                "POST /api/embeddings/generate"
            ]
        },
        {
            "name": "Gmail Notifications",
            "description": "Emails automatisés",
            "endpoints": [
                "POST /api/test-email",
                "GET /api/email-config",
                "POST /api/send-market-report-email"
            ]
        },
        {
            "name": "Analytics Avancés",
            "description": "Analytics du portefeuille",
            "endpoint": "GET /api/analytics/advanced",
            "features": ["Performance par catégorie", "Métriques financières", "KPIs"]
        },
        {
            "name": "Rapports PDF",
            "description": "Génération de rapports",
            "endpoints": [
                "GET /api/portfolio/pdf",
                "GET /api/reports/asset-class/<name>",
                "GET /api/reports/all-asset-classes"
            ]
        }
    ]
    
    for integration in integrations:
        print(f"\n📊 {integration['name']}")
        print(f"   📝 {integration['description']}")
        
        if 'endpoint' in integration:
            print(f"   🔗 {integration['endpoint']}")
        elif 'endpoints' in integration:
            print("   🔗 Endpoints:")
            for endpoint in integration['endpoints']:
                print(f"      - {endpoint}")
        
        if 'config' in integration:
            print(f"   ⚙️  Config: {integration['config']}")
        
        if 'features' in integration:
            print("   ✨ Fonctionnalités:")
            for feature in integration['features']:
                print(f"      - {feature}")

def list_web_interfaces():
    """Liste les interfaces web"""
    print("\n🌐 INTERFACES WEB")
    print("-" * 50)
    
    interfaces = [
        {
            "name": "Application Principale",
            "url": "/",
            "template": "templates/index.html",
            "description": "Page d'accueil"
        },
        {
            "name": "Analytics",
            "url": "/analytics",
            "template": "templates/analytics.html",
            "description": "Analytics avancés"
        },
        {
            "name": "Rapports",
            "url": "/reports",
            "template": "templates/reports.html",
            "description": "Rapports et PDFs"
        },
        {
            "name": "Marchés",
            "url": "/markets",
            "template": "templates/markets.html",
            "description": "Informations de marché"
        },
        {
            "name": "Configuration",
            "url": "/settings",
            "template": "templates/settings.html",
            "description": "Configuration"
        },
        {
            "name": "Items Vendus",
            "url": "/sold",
            "template": "templates/sold.html",
            "description": "Items vendus"
        },
        {
            "name": "OpenAI Web Search",
            "url": "/web-search",
            "template": "templates/web_search.html",
            "description": "Interface test OpenAI Web Search"
        },
        {
            "name": "Google Search API",
            "url": "/google-search",
            "template": "templates/google_search.html",
            "description": "Interface test Google Search API"
        }
    ]
    
    for interface in interfaces:
        status = "✅" if check_file_exists(interface['template']) else "❌"
        print(f"{status} {interface['name']}")
        print(f"   🌐 URL: http://localhost:5000{interface['url']}")
        print(f"   📁 Template: {interface['template']} ({get_file_size(interface['template'])})")
        print(f"   📝 {interface['description']}")
        print()

def list_test_files():
    """Liste les fichiers de test"""
    print("\n🧪 FICHIERS DE TEST")
    print("-" * 50)
    
    test_files = [
        "test_web_search_integration.py",
        "test_google_search_integration.py",
        "test_manus_integration.py",
        "test_yahoo_finance.py",
        "test_alpha_vantage.py",
        "test_fallback_system.py",
        "test_rate_limiting.py",
        "test_production_final.py",
        "debug_price_issue.py",
        "debug_webapp_vs_local.py",
        "test_tsla_price_issue.py"
    ]
    
    for test_file in test_files:
        status = "✅" if check_file_exists(test_file) else "❌"
        size = get_file_size(test_file)
        print(f"{status} {test_file} ({size})")

def list_documentation():
    """Liste la documentation"""
    print("\n📚 DOCUMENTATION")
    print("-" * 50)
    
    docs = [
        "WEB_SEARCH_IMPLEMENTATION.md",
        "WEB_SEARCH_SUMMARY.md",
        "GOOGLE_SEARCH_IMPLEMENTATION.md",
        "GOOGLE_SEARCH_SUMMARY.md",
        "MANUS_APIS_INTEGRATION_SUMMARY.md",
        "INTEGRATIONS_OVERVIEW.md"
    ]
    
    for doc in docs:
        status = "✅" if check_file_exists(doc) else "❌"
        size = get_file_size(doc)
        print(f"{status} {doc} ({size})")

def check_environment_variables():
    """Vérifie les variables d'environnement"""
    print("\n⚙️ VARIABLES D'ENVIRONNEMENT")
    print("-" * 50)
    
    env_vars = [
        "OPENAI_API_KEY",
        "GOOGLE_SEARCH_API_KEY",
        "GOOGLE_SEARCH_ENGINE_ID",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "FREECURRENCY_API_KEY",
        "GMAIL_USER",
        "GMAIL_PASSWORD"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        display_value = "Configuré" if value else "Non configuré"
        print(f"{status} {var}: {display_value}")

def generate_summary():
    """Génère un résumé des intégrations"""
    print("\n📊 RÉSUMÉ DES INTÉGRATIONS")
    print("-" * 50)
    
    # Compter les fichiers
    total_files = len([f for f in os.listdir('.') if f.endswith('.py')])
    test_files = len([f for f in os.listdir('.') if f.startswith('test_')])
    doc_files = len([f for f in os.listdir('.') if f.endswith('.md')])
    
    print(f"📁 Fichiers Python: {total_files}")
    print(f"🧪 Fichiers de test: {test_files}")
    print(f"📚 Fichiers de documentation: {doc_files}")
    
    # Vérifier les intégrations principales
    main_integrations = [
        "web_search_manager.py",
        "google_search_manager.py",
        "manus_integration.py",
        "yahoo_finance_api.py",
        "alpha_vantage_fallback.py"
    ]
    
    available = sum(1 for f in main_integrations if check_file_exists(f))
    print(f"🔗 Intégrations principales: {available}/{len(main_integrations)}")
    
    # Vérifier les interfaces web
    templates = [
        "templates/index.html",
        "templates/analytics.html",
        "templates/reports.html",
        "templates/markets.html",
        "templates/settings.html",
        "templates/sold.html",
        "templates/web_search.html",
        "templates/google_search.html"
    ]
    
    available_templates = sum(1 for t in templates if check_file_exists(t))
    print(f"🌐 Templates web: {available_templates}/{len(templates)}")

def main():
    """Fonction principale"""
    print_header()
    
    list_search_integrations()
    list_stock_integrations()
    list_other_integrations()
    list_web_interfaces()
    list_test_files()
    list_documentation()
    check_environment_variables()
    generate_summary()
    
    print("\n" + "=" * 80)
    print("🎯 POUR UTILISER LES INTÉGRATIONS:")
    print("1. Configurez les variables d'environnement")
    print("2. Démarrez l'application: python app.py")
    print("3. Accédez aux interfaces: http://localhost:5000")
    print("4. Testez les APIs avec les scripts de test")
    print("=" * 80)

if __name__ == "__main__":
    main() 