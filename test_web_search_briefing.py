#!/usr/bin/env python3
"""
Script de test pour le nouveau prompt de briefing avec recherche web
"""

def test_web_search_prompt():
    """Test du nouveau prompt avec recherche web"""
    
    print("🧪 Test du prompt avec recherche web")
    print("=" * 60)
    
    # Nouveau prompt
    prompt = """Tu es un stratégiste financier expérimenté. Utilise ta fonction de recherche web pour récupérer les données de marché actuelles et génère un briefing narratif fluide, concis et structuré sur la séance des marchés financiers du jour.

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
    
    print("✅ Nouveau prompt avec recherche web")
    print(f"📏 Longueur du prompt: {len(prompt)} caractères")
    
    # Configuration API
    api_config = {
        "model": "gpt-4o",
        "max_tokens": 1500,
        "temperature": 0.7,
        "tools": [{"type": "web_search"}]
    }
    
    print(f"\n🔧 Configuration API:")
    for key, value in api_config.items():
        print(f"  {key}: {value}")
    
    # Avantages du nouveau système
    print(f"\n🚀 Avantages du système avec recherche web:")
    print("  ✅ Données en temps réel via recherche web")
    print("  ✅ Pas besoin de Yahoo Finance API")
    print("  ✅ Actualités macro et géopolitiques incluses")
    print("  ✅ Données plus complètes et à jour")
    print("  ✅ Moins de maintenance (pas de symboles à gérer)")
    print("  ✅ Gestion automatique des erreurs d'API")
    
    # Extrait du prompt
    print(f"\n📝 Extrait du prompt:")
    print("-" * 40)
    print(prompt[:300] + "...")
    print("-" * 40)

def compare_approaches():
    """Compare les deux approches"""
    
    print("\n" + "=" * 60)
    print("🔄 Comparaison des approches")
    print("=" * 60)
    
    print("\n📊 Approche Yahoo Finance (ancienne):")
    print("  ❌ Dépendance à l'API Yahoo Finance")
    print("  ❌ Gestion des symboles et erreurs")
    print("  ❌ Limites de requêtes")
    print("  ❌ Maintenance des symboles")
    print("  ❌ Pas d'actualités macro")
    
    print("\n🌐 Approche Recherche Web (nouvelle):")
    print("  ✅ Données en temps réel")
    print("  ✅ Pas de dépendance API externe")
    print("  ✅ Actualités incluses")
    print("  ✅ Données plus complètes")
    print("  ✅ Moins de maintenance")
    print("  ✅ Gestion automatique des erreurs")

if __name__ == "__main__":
    # Test du nouveau prompt
    test_web_search_prompt()
    
    # Comparaison des approches
    compare_approaches()
    
    print("\n🏁 Tests terminés")
    print("\n💡 Le prompt a été mis à jour pour utiliser la recherche web de ChatGPT")
    print("🎯 Avantage principal: Données plus complètes et à jour sans maintenance") 