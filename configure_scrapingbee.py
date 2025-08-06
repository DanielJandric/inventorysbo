#!/usr/bin/env python3
"""
Script de configuration pour ScrapingBee
"""

import os
import sys
from dotenv import load_dotenv

def configure_scrapingbee():
    """Configure ScrapingBee API"""
    print("🐝 Configuration ScrapingBee")
    print("=" * 50)
    
    # Charger les variables d'environnement existantes
    load_dotenv()
    
    # Vérifier si la clé existe déjà
    existing_key = os.getenv('SCRAPINGBEE_API_KEY')
    if existing_key:
        print(f"✅ Clé ScrapingBee existante trouvée: {existing_key[:10]}...")
        choice = input("Voulez-vous la remplacer ? (y/N): ").lower()
        if choice != 'y':
            print("Configuration annulée.")
            return
    
    print("\n📋 Instructions pour obtenir votre clé ScrapingBee:")
    print("1. Allez sur https://www.scrapingbee.com/")
    print("2. Créez un compte gratuit")
    print("3. Obtenez votre clé API dans le dashboard")
    print("4. Copiez la clé ci-dessous")
    print()
    
    # Demander la clé API
    api_key = input("🔑 Entrez votre clé ScrapingBee API: ").strip()
    
    if not api_key:
        print("❌ Clé API requise")
        return
    
    # Mettre à jour le fichier .env
    env_file = '.env'
    env_content = ""
    
    # Lire le contenu existant
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
    
    # Ajouter ou mettre à jour la clé ScrapingBee
    lines = env_content.split('\n')
    scrapingbee_line = f"SCRAPINGBEE_API_KEY={api_key}"
    
    # Chercher si la ligne existe déjà
    found = False
    for i, line in enumerate(lines):
        if line.startswith('SCRAPINGBEE_API_KEY='):
            lines[i] = scrapingbee_line
            found = True
            break
    
    if not found:
        lines.append(scrapingbee_line)
    
    # Écrire le fichier .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Clé ScrapingBee sauvegardée dans {env_file}")
    
    # Tester la configuration
    print("\n🧪 Test de la configuration...")
    test_scrapingbee_config()

def test_scrapingbee_config():
    """Teste la configuration ScrapingBee"""
    try:
        from scrapingbee_scraper import get_scrapingbee_scraper
        
        scraper = get_scrapingbee_scraper()
        scraper.initialize_sync()
        
        print("✅ Configuration ScrapingBee valide")
        print("✅ Scraper initialisé avec succès")
        
        # Test simple
        print("\n🔍 Test de recherche simple...")
        import asyncio
        
        async def test_search():
            task_id = await scraper.create_scraping_task("test", 1)
            result = await scraper.execute_scraping_task(task_id)
            return result
        
        result = asyncio.run(test_search())
        
        if "error" in result:
            print(f"⚠️ Test échoué: {result['error']}")
            print("💡 Vérifiez votre clé API et votre quota")
        else:
            print("✅ Test de scraping réussi")
            print("🎉 Configuration ScrapingBee complète !")
        
    except Exception as e:
        print(f"❌ Erreur de test: {e}")
        print("💡 Vérifiez votre clé API ScrapingBee")

def show_scrapingbee_info():
    """Affiche les informations sur ScrapingBee"""
    print("\n📚 Informations ScrapingBee:")
    print("• Service de web scraping professionnel")
    print("• Anti-détection intégrée")
    print("• Rotation automatique de proxies")
    print("• API REST simple")
    print("• Plan gratuit: 1000 requêtes/mois")
    print("• Pas de gestion de navigateur nécessaire")
    print()
    print("🔗 Site web: https://www.scrapingbee.com/")
    print("📖 Documentation: https://www.scrapingbee.com/docs/")

if __name__ == "__main__":
    print("🐝 Configuration ScrapingBee pour InventorySBO")
    print("=" * 60)
    
    show_scrapingbee_info()
    
    choice = input("\nVoulez-vous configurer ScrapingBee maintenant ? (Y/n): ").lower()
    if choice != 'n':
        configure_scrapingbee()
    else:
        print("Configuration annulée.") 