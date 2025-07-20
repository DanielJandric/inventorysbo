#!/usr/bin/env python3
"""
Script de test pour vérifier l'agrégation des actions dans les statistiques
"""

import requests
import json

def test_stock_aggregation():
    """Test de l'agrégation des actions dans les statistiques"""
    
    print("🧪 Test de l'agrégation des actions dans les statistiques")
    print("=" * 60)
    
    # URL de base
    base_url = "http://localhost:5000"
    
    try:
        # 1. Récupérer tous les items
        print("📊 Récupération des items...")
        response = requests.get(f"{base_url}/api/items")
        
        if response.status_code != 200:
            print(f"❌ Erreur récupération items: {response.status_code}")
            return False
        
        items = response.json()
        print(f"✅ {len(items)} items récupérés")
        
        # 2. Identifier les actions
        actions = [item for item in items if item.get('category') == 'Actions']
        print(f"📈 {len(actions)} actions trouvées")
        
        # 3. Analyser chaque action
        total_action_value = 0
        for action in actions:
            symbol = action.get('stock_symbol', 'N/A')
            quantity = action.get('stock_quantity', 0)
            current_price = action.get('current_price', 0)
            current_value = action.get('current_value', 0)
            
            calculated_value = current_price * quantity if current_price and quantity else 0
            
            print(f"   - {symbol}: {current_price} × {quantity} = {calculated_value} CHF (DB: {current_value})")
            
            if calculated_value != current_value:
                print(f"     ⚠️ Valeur calculée ({calculated_value}) ≠ valeur DB ({current_value})")
            
            total_action_value += calculated_value
        
        print(f"\n💰 Valeur totale des actions: {total_action_value:,.0f} CHF")
        
        # 4. Calculer la valeur totale disponible
        available_items = [item for item in items if item.get('status') == 'Available']
        total_available_value = 0
        
        for item in available_items:
            if item.get('category') == 'Actions':
                # Pour les actions : prix × quantité
                value = (item.get('current_price', 0) * item.get('stock_quantity', 0))
            else:
                # Pour les autres objets : current_value
                value = item.get('current_value', 0)
            
            total_available_value += value
        
        print(f"💼 Valeur totale disponible: {total_available_value:,.0f} CHF")
        
        # 5. Vérifier les analytics
        print("\n📊 Vérification des analytics...")
        analytics_response = requests.get(f"{base_url}/api/analytics/advanced")
        
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            financial_metrics = analytics.get('financial_metrics', {})
            
            total_value_analytics = financial_metrics.get('total_value', 0)
            print(f"📈 Valeur totale dans analytics: {total_value_analytics:,.0f} CHF")
            
            if abs(total_available_value - total_value_analytics) > 1:
                print(f"⚠️ Différence entre calcul ({total_available_value:,.0f}) et analytics ({total_value_analytics:,.0f})")
            else:
                print("✅ Valeurs cohérentes")
        else:
            print(f"❌ Erreur analytics: {analytics_response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à {base_url}")
        print(f"   Assurez-vous que l'application Flask est démarrée")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_stock_aggregation() 