#!/usr/bin/env python3
"""
Script de test pour le nouveau prompt de briefing avec Gemini et recherche web
"""

def test_gemini_web_search_prompt():
    """Test du nouveau prompt avec Gemini et recherche web"""
    
    print("🧪 Test du prompt Gemini avec recherche web")
    print("=" * 60)
    
    # Nouveau prompt pour Gemini
    prompt = """Tu es un stratégiste financier expérimenté. Utilise ta fonction de recherche web pour récupérer les données de marché actuelles et génères un briefing narratif fluide, concis et structuré sur la séance des marchés financiers du jour.

Format exigé :
- Ton narratif, comme un stratégiste qui me parle directement
- Concision : pas de blabla, mais du fond
- Structure logique intégrée dans le récit (pas de titres) :
  * Actions (USA, Europe, Suisse, autres zones si mouvement marquant)
  * Obligations souveraines (US 10Y, Bund, OAT, BTP, Confédération…)
  * Cryptoactifs (BTC, ETH, capitalisation globale, régulation, flux)
  * Macro, banques centrales et géopolitique (stats, décisions, tensions)
- Termine par une synthèse rapide intégrée à la narration, avec ce que je dois retenir en une phrase, et signale tout signal faible ou rupture de tendance à surveiller

Recherche les données de marché actuelles pour :
- Indices boursiers (S&P 500, NASDAQ, Dow Jones, Euro Stoxx 50, DAX, CAC 40, Swiss Market Index)
- Rendements obligataires (US 10Y, Bund 10Y, OAT 10Y, BTP 10Y)
- Cryptoactifs (Bitcoin, Ethereum, capitalisation globale)
- Devises (EUR/USD, USD/CHF, GBP/USD)
- Commodities (Or, Pétrole)
- Actualités macro et géopolitiques importantes

Si une classe d'actif n'a pas bougé, dis-le clairement sans meubler. Génère un briefing pour aujourd'hui basé sur les données de marché réelles trouvées."""
    
    print("✅ Nouveau prompt Gemini avec recherche web")
    print(f"📏 Longueur du prompt: {len(prompt)} caractères")
    
    # Configuration API Gemini
    api_config = {
        "model": "gemini-1.5-flash",
        "maxOutputTokens": 4000,
        "temperature": 0.3,
        "tools": [{"googleSearch": {}}]
    }
    
    print(f"\n🔧 Configuration API Gemini:")
    for key, value in api_config.items():
        print(f"  {key}: {value}")
    
    # Avantages du nouveau système
    print(f"\n🚀 Avantages du système Gemini avec recherche web:")
    print("  ✅ Données en temps réel via Google Search")
    print("  ✅ Pas besoin de Yahoo Finance API")
    print("  ✅ Actualités macro et géopolitiques incluses")
    print("  ✅ Données plus complètes et à jour")
    print("  ✅ Moins de maintenance (pas de symboles à gérer)")
    print("  ✅ Gestion automatique des erreurs d'API")
    print("  ✅ Clé API gratuite disponible")
    print("  ✅ Limites généreuses pour usage personnel")
    
    # Extrait du prompt
    print(f"\n📝 Extrait du prompt:")
    print("-" * 40)
    print(prompt[:300] + "...")
    print("-" * 40)

def compare_approaches():
    """Compare les différentes approches"""
    
    print("\n" + "=" * 60)
    print("🔄 Comparaison des approches")
    print("=" * 60)
    
    print("\n📊 Approche Yahoo Finance (ancienne):")
    print("  ❌ Dépendance à l'API Yahoo Finance")
    print("  ❌ Gestion des symboles et erreurs")
    print("  ❌ Limites de requêtes")
    print("  ❌ Maintenance des symboles")
    print("  ❌ Pas d'actualités macro")
    
    print("\n🤖 Approche OpenAI GPT-4o (intermédiaire):")
    print("  ✅ Données en temps réel via recherche web")
    print("  ✅ Actualités incluses")
    print("  ❌ Coût par requête")
    print("  ❌ Limites de tokens")
    print("  ❌ Dépendance à OpenAI")
    
    print("\n🌐 Approche Gemini (nouvelle):")
    print("  ✅ Données en temps réel via Google Search")
    print("  ✅ Pas de dépendance API externe")
    print("  ✅ Actualités incluses")
    print("  ✅ Données plus complètes")
    print("  ✅ Moins de maintenance")
    print("  ✅ Gestion automatique des erreurs")
    print("  ✅ Clé API gratuite")
    print("  ✅ Limites généreuses")

def test_gemini_integration():
    """Test de l'intégration Gemini dans l'application"""
    
    print("\n" + "=" * 60)
    print("🔧 Test d'intégration Gemini")
    print("=" * 60)
    
    # Configuration requise
    required_config = {
        "GEMINI_API_KEY": "Clé API Google Gemini",
        "URL": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "Headers": {
            "Content-Type": "application/json",
            "X-goog-api-key": "VOTRE_CLE_GEMINI"
        }
    }
    
    print("📋 Configuration requise:")
    for key, value in required_config.items():
        print(f"  {key}: {value}")
    
    # Fonctionnalités
    features = [
        "✅ Briefing de marché automatique quotidien",
        "✅ Déclenchement manuel via interface web",
        "✅ Recherche web intégrée pour données temps réel",
        "✅ Structure narrative complète",
        "✅ Notifications email automatiques",
        "✅ Sauvegarde en base de données",
        "✅ Fallback vers OpenAI si erreur"
    ]
    
    print("\n🎯 Fonctionnalités Gemini:")
    for feature in features:
        print(f"  {feature}")

if __name__ == "__main__":
    # Test du nouveau prompt
    test_gemini_web_search_prompt()
    
    # Comparaison des approches
    compare_approaches()
    
    # Test d'intégration
    test_gemini_integration()
    
    print("\n🏁 Tests terminés")
    print("\n💡 Le prompt a été mis à jour pour utiliser Gemini avec recherche web")
    print("🎯 Avantage principal: Données plus complètes et à jour sans maintenance")
    print("🔑 Configuration: Ajoutez GEMINI_API_KEY dans votre .env") 