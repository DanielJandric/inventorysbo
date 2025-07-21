#!/usr/bin/env python3
"""
Test pour vérifier si l'API Manus envoie bien le P/E ratio
"""

import requests
import json
from datetime import datetime

def test_manus_pe_ratio():
    """Test de l'API Manus pour le P/E ratio"""
    
    print("🔍 Test de l'API Manus pour le P/E ratio...")
    
    # Configuration
    api_base = "https://g8h3ilcvpz3y.manus.space"
    
    # Symboles de test (actions connues avec P/E ratio)
    test_symbols = [
        "AAPL",    # Apple (USA)
        "MSFT",    # Microsoft (USA)
        "GOOGL",   # Google (USA)
        "NESTLE.SW", # Nestlé (Suisse)
        "NOVN.SW", # Novartis (Suisse)
        "ROG.SW",  # Roche (Suisse)
        "ASML",    # ASML (Pays-Bas)
        "SAP",     # SAP (Allemagne)
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print(f"\n📊 Test de {len(test_symbols)} symboles...")
    print("="*80)
    
    results = []
    
    for symbol in test_symbols:
        try:
            print(f"\n🔍 Test de {symbol}...")
            
            # Déterminer la région
            if symbol.endswith('.SW'):
                region = 'CH'  # Suisse
            elif symbol in ['ASML', 'SAP']:
                region = 'EU'  # Europe
            else:
                region = 'US'  # USA
            
            # Appel API Manus
            url = f"{api_base}/api/custom/stocks"
            params = {
                'symbols': symbol,
                'region': region
            }
            
            print(f"   URL: {url}")
            print(f"   Paramètres: {params}")
            
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"   Status: {response.status_code}")
            print(f"   Success: {data.get('success', False)}")
            
            if data.get('success') and data.get('data'):
                stock_data = data['data'][0]
                
                # Extraire les données importantes
                result = {
                    'symbol': symbol,
                    'name': stock_data.get('name', 'N/A'),
                    'price': stock_data.get('price', 0),
                    'currency': stock_data.get('currency', 'N/A'),
                    'pe_ratio': stock_data.get('pe_ratio', 'N/A'),
                    'pe_ratio_type': type(stock_data.get('pe_ratio')).__name__,
                    'volume': stock_data.get('volume', 0),
                    'change_percent': stock_data.get('change_percent', 0),
                    'exchange': stock_data.get('exchange', 'N/A'),
                    'region': region,
                    'all_fields': list(stock_data.keys())
                }
                
                results.append(result)
                
                print(f"   ✅ Données récupérées:")
                print(f"      - Nom: {result['name']}")
                print(f"      - Prix: {result['price']} {result['currency']}")
                print(f"      - P/E Ratio: {result['pe_ratio']} (type: {result['pe_ratio_type']})")
                print(f"      - Volume: {result['volume']}")
                print(f"      - Variation: {result['change_percent']}%")
                print(f"      - Exchange: {result['exchange']}")
                print(f"      - Champs disponibles: {len(result['all_fields'])}")
                
            else:
                print(f"   ❌ Aucune donnée trouvée")
                results.append({
                    'symbol': symbol,
                    'error': 'Aucune donnée',
                    'region': region
                })
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erreur API: {e}")
            results.append({
                'symbol': symbol,
                'error': f'Erreur API: {e}',
                'region': region
            })
        except Exception as e:
            print(f"   ❌ Erreur inattendue: {e}")
            results.append({
                'symbol': symbol,
                'error': f'Erreur: {e}',
                'region': region
            })
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"✅ Succès: {len(successful)}/{len(results)}")
    print(f"❌ Échecs: {len(failed)}/{len(results)}")
    
    if successful:
        print(f"\n📈 P/E RATIOS RÉCUPÉRÉS:")
        for result in successful:
            pe_status = "✅" if result['pe_ratio'] not in [0, None, 'N/A'] else "❌"
            print(f"   {pe_status} {result['symbol']}: {result['pe_ratio']} ({result['pe_ratio_type']})")
        
        # Statistiques P/E
        pe_values = [r['pe_ratio'] for r in successful if r['pe_ratio'] not in [0, None, 'N/A']]
        if pe_values:
            print(f"\n📊 Statistiques P/E:")
            print(f"   - Nombre de P/E valides: {len(pe_values)}")
            print(f"   - P/E moyen: {sum(pe_values) / len(pe_values):.2f}")
            print(f"   - P/E min: {min(pe_values):.2f}")
            print(f"   - P/E max: {max(pe_values):.2f}")
    
    if failed:
        print(f"\n❌ ÉCHECS:")
        for result in failed:
            print(f"   - {result['symbol']}: {result['error']}")
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"test_manus_pe_ratio_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'pe_ratios_found': len([r for r in successful if r['pe_ratio'] not in [0, None, 'N/A']])
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans {filename}")
    print("\n✅ Test terminé !")

if __name__ == "__main__":
    test_manus_pe_ratio() 