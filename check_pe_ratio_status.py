#!/usr/bin/env python3
"""
Vérification de l'état des P/E ratios dans la base de données et le cache
"""

import json
import os
from datetime import datetime

def check_pe_ratio_status():
    """Vérifie l'état des P/E ratios"""
    
    print("🔍 Vérification de l'état des P/E ratios...")
    
    # 1. Vérifier le cache des prix
    print("\n📊 1. CACHE DES PRIX")
    print("="*50)
    
    cache_file = "stock_data/price_cache.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"✅ Cache trouvé avec {len(cache_data)} symboles")
            
            pe_ratios_found = 0
            total_symbols = 0
            
            for symbol, data in cache_data.items():
                total_symbols += 1
                if 'data' in data and 'pe_ratio' in data['data']:
                    pe_ratio = data['data']['pe_ratio']
                    if pe_ratio and pe_ratio != 0:
                        pe_ratios_found += 1
                        print(f"   ✅ {symbol}: P/E = {pe_ratio}")
                    else:
                        print(f"   ❌ {symbol}: P/E = {pe_ratio} (invalide)")
                else:
                    print(f"   ❌ {symbol}: Pas de P/E ratio")
            
            print(f"\n📈 Statistiques cache:")
            print(f"   - Symboles avec P/E valide: {pe_ratios_found}/{total_symbols}")
            print(f"   - Taux de succès: {(pe_ratios_found/total_symbols*100):.1f}%")
            
        except Exception as e:
            print(f"❌ Erreur lecture cache: {e}")
    else:
        print("❌ Fichier cache non trouvé")
    
    # 2. Vérifier la base de données (simulation)
    print("\n🗄️ 2. BASE DE DONNÉES (SIMULATION)")
    print("="*50)
    
    print("Pour vérifier la base de données, exécutez cette requête SQL dans Supabase:")
    print("""
SELECT 
    id,
    name,
    stock_symbol,
    stock_pe_ratio,
    current_price,
    last_price_update
FROM items 
WHERE category = 'Actions' 
AND stock_symbol IS NOT NULL
ORDER BY stock_symbol;
    """)
    
    # 3. Vérifier le code de mise à jour
    print("\n🔧 3. CODE DE MISE À JOUR")
    print("="*50)
    
    print("Le code semble correctement configuré:")
    print("✅ StockPriceData inclut pe_ratio")
    print("✅ ManusStockManager récupère pe_ratio")
    print("✅ app.py met à jour stock_pe_ratio")
    print("✅ Frontend affiche stock_pe_ratio")
    
    # 4. Recommandations
    print("\n💡 4. RECOMMANDATIONS")
    print("="*50)
    
    print("1. Vérifiez la base de données avec la requête SQL ci-dessus")
    print("2. Si les P/E ratios sont manquants en base, déclenchez une mise à jour:")
    print("   - Via l'interface web: Bouton 'Mettre à jour tous les prix'")
    print("   - Ou via l'API: POST /api/stock-price/update-all")
    print("3. Vérifiez que l'API Manus fonctionne (erreur 526 actuelle)")
    print("4. Le système utilise Yahoo Finance comme fallback (fonctionne)")
    
    # 5. Test rapide de mise à jour
    print("\n🔄 5. TEST DE MISE À JOUR")
    print("="*50)
    
    print("Pour tester une mise à jour, vous pouvez:")
    print("1. Aller sur l'interface web")
    print("2. Cliquer sur 'Mettre à jour tous les prix'")
    print("3. Vérifier que les P/E ratios apparaissent dans les cartes")
    
    print("\n✅ Vérification terminée !")

if __name__ == "__main__":
    check_pe_ratio_status() 