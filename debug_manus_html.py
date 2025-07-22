#!/usr/bin/env python3
"""
Debug du contenu HTML de l'API Manus pour identifier les patterns corrects
"""

import requests
import re
from datetime import datetime

def analyze_manus_html():
    """Analyse le contenu HTML de l'API Manus"""
    print("🔍 Analyse du contenu HTML de l'API Manus...")
    
    base_url = "https://ogh5izcelen1.manus.space"
    symbol = "TSLA"
    
    try:
        # Récupérer le contenu HTML
        response = requests.get(f"{base_url}/api/stocks/{symbol}", timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            print(f"📊 Taille du contenu: {len(html_content)} caractères")
            
            # Sauvegarder le contenu pour analyse
            with open(f"manus_html_debug_{symbol}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"💾 Contenu sauvegardé dans manus_html_debug_{symbol}.html")
            
            # Analyser le contenu
            analyze_content(html_content, symbol)
            
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def analyze_content(html_content, symbol):
    """Analyse le contenu HTML pour trouver les patterns"""
    print(f"\n🔍 Analyse du contenu pour {symbol}...")
    
    # Chercher des patterns de prix
    price_patterns = [
        r'price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
        r'current-price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
        r'[\$€£]?\s*([\d,]+\.?\d*)\s*USD?',
        r'price["\']?\s*=\s*["\']?([\d,]+\.?\d*)["\']?',
        r'value["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
        r'amount["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
        r'[\$€£]?\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*USD?',
        r'([\d,]+\.?\d*)\s*\$',
        r'([\d,]+\.?\d*)\s*€',
        r'([\d,]+\.?\d*)\s*£'
    ]
    
    print("🔍 Recherche de patterns de prix...")
    for i, pattern in enumerate(price_patterns):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"   Pattern {i+1}: {len(matches)} matches trouvés")
            for j, match in enumerate(matches[:5]):  # Afficher les 5 premiers
                print(f"     Match {j+1}: '{match}'")
    
    # Chercher des patterns de changement
    change_patterns = [
        r'change["\']?\s*:\s*["\']?([+-]?[\d,]+\.?\d*)["\']?',
        r'[\$€£]?\s*([+-]?[\d,]+\.?\d*)\s*\([+-]?\d+\.?\d*%\)',
        r'([+-]?[\d,]+\.?\d*)\s*\([+-]?\d+\.?\d*%\)',
        r'([+-]?[\d,]+\.?\d*)%',
        r'([+-]?[\d,]+\.?\d*)\s*points'
    ]
    
    print("\n🔍 Recherche de patterns de changement...")
    for i, pattern in enumerate(change_patterns):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"   Pattern {i+1}: {len(matches)} matches trouvés")
            for j, match in enumerate(matches[:3]):  # Afficher les 3 premiers
                print(f"     Match {j+1}: '{match}'")
    
    # Chercher des patterns de pourcentage
    percent_patterns = [
        r'change-percent["\']?\s*:\s*["\']?([+-]?[\d,]+\.?\d*)%["\']?',
        r'\(([+-]?[\d,]+\.?\d*)%\)',
        r'([+-]?[\d,]+\.?\d*)%',
        r'percent["\']?\s*:\s*["\']?([+-]?[\d,]+\.?\d*)["\']?'
    ]
    
    print("\n🔍 Recherche de patterns de pourcentage...")
    for i, pattern in enumerate(percent_patterns):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"   Pattern {i+1}: {len(matches)} matches trouvés")
            for j, match in enumerate(matches[:3]):  # Afficher les 3 premiers
                print(f"     Match {j+1}: '{match}'")
    
    # Chercher des patterns de volume
    volume_patterns = [
        r'volume["\']?\s*:\s*["\']?([\d,]+)["\']?',
        r'volume["\']?\s*=\s*["\']?([\d,]+)["\']?',
        r'([\d,]+)\s*shares',
        r'([\d,]+)\s*volume'
    ]
    
    print("\n🔍 Recherche de patterns de volume...")
    for i, pattern in enumerate(volume_patterns):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"   Pattern {i+1}: {len(matches)} matches trouvés")
            for j, match in enumerate(matches[:3]):  # Afficher les 3 premiers
                print(f"     Match {j+1}: '{match}'")
    
    # Analyser la structure JSON si présente
    print("\n🔍 Recherche de structure JSON...")
    json_patterns = [
        r'\{[^{}]*"price"[^{}]*\}',
        r'\{[^{}]*"value"[^{}]*\}',
        r'\{[^{}]*"amount"[^{}]*\}'
    ]
    
    for i, pattern in enumerate(json_patterns):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"   JSON Pattern {i+1}: {len(matches)} matches trouvés")
            for j, match in enumerate(matches[:2]):  # Afficher les 2 premiers
                print(f"     JSON {j+1}: '{match[:100]}...'")
    
    # Chercher des balises HTML avec des prix
    html_patterns = [
        r'<span[^>]*>[\$€£]?\s*([\d,]+\.?\d*)</span>',
        r'<div[^>]*>[\$€£]?\s*([\d,]+\.?\d*)</div>',
        r'<td[^>]*>[\$€£]?\s*([\d,]+\.?\d*)</td>',
        r'<span[^>]*>([\d,]+\.?\d*)</span>',
        r'<div[^>]*>([\d,]+\.?\d*)</div>'
    ]
    
    print("\n🔍 Recherche de balises HTML avec prix...")
    for i, pattern in enumerate(html_patterns):
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"   HTML Pattern {i+1}: {len(matches)} matches trouvés")
            for j, match in enumerate(matches[:3]):  # Afficher les 3 premiers
                print(f"     HTML {j+1}: '{match}'")

def test_current_patterns():
    """Test des patterns actuels"""
    print("\n🔍 Test des patterns actuels...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test avec force_refresh pour voir les logs
        result = manus_stock_api.get_stock_price("TSLA", force_refresh=True)
        
        print(f"📊 Résultat actuel: {result}")
        
        if result.get('parsing_success'):
            print("✅ Parsing réussi avec les patterns actuels")
            print(f"💰 Prix extrait: {result.get('price')}")
        else:
            print("❌ Parsing échoué avec les patterns actuels")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur test patterns: {e}")
        return None

def suggest_improvements():
    """Suggestions d'amélioration basées sur l'analyse"""
    print("\n🔍 Suggestions d'amélioration...")
    
    suggestions = [
        "1. Analyser le fichier manus_html_debug_TSLA.html pour identifier les vrais patterns",
        "2. Ajuster les patterns regex selon la structure HTML réelle",
        "3. Ajouter des patterns spécifiques pour les balises HTML",
        "4. Implémenter un parsing JSON si les données sont en JSON",
        "5. Ajouter des patterns pour les métriques manquantes (volume, PE, etc.)",
        "6. Tester avec différents symboles pour valider les patterns"
    ]
    
    for suggestion in suggestions:
        print(f"   💡 {suggestion}")

def main():
    """Fonction principale"""
    print("🚀 Debug du contenu HTML de l'API Manus")
    print("=" * 80)
    
    # Analyser le contenu HTML
    analyze_manus_html()
    
    # Tester les patterns actuels
    test_current_patterns()
    
    # Suggestions
    suggest_improvements()
    
    print("\n" + "=" * 80)
    print("📋 PROCHAINES ÉTAPES:")
    print("1. Examiner le fichier manus_html_debug_TSLA.html")
    print("2. Identifier les vrais patterns de prix")
    print("3. Mettre à jour les patterns regex")
    print("4. Tester avec les nouveaux patterns")
    print("5. Valider avec plusieurs symboles")

if __name__ == "__main__":
    main() 