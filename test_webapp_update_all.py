#!/usr/bin/env python3
"""
Script de test pour l'endpoint webapp update-all après correction
"""

import requests
import json

def test_webapp_update_all():
    """Test de l'endpoint /api/stock-price/update-all"""
    
    print("🧪 Test de l'endpoint webapp update-all")
    print("=" * 50)
    
    # URL de base (remplacez par votre URL si différente)
    base_url = "http://localhost:5000"
    
    try:
        print("🔄 Appel de l'endpoint /api/stock-price/update-all...")
        response = requests.post(f"{base_url}/api/stock-price/update-all")
        
        print(f"📊 Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Succès!")
            print(f"   - Message: {data.get('message', 'N/A')}")
            print(f"   - Symboles traités: {data.get('updated_count', 'N/A')}")
            print(f"   - Total actions: {data.get('total_actions', 'N/A')}")
            print(f"   - Requêtes utilisées: {data.get('requests_used', 'N/A')}")
            print(f"   - Cache utilisé: {data.get('cache_used', 'N/A')}")
            print(f"   - Ignorés: {data.get('skipped_count', 'N/A')}")
            print(f"   - Échecs: {data.get('failed_count', 'N/A')}")
            
            # Vérifier que 'errors' n'existe pas
            if 'errors' in data:
                print(f"❌ ERREUR: La clé 'errors' existe encore dans la réponse!")
                return False
            else:
                print(f"✅ OK: La clé 'errors' n'existe pas dans la réponse")
            
            # Vérifier que 'failed' existe
            if 'failed' in data:
                print(f"✅ OK: La clé 'failed' existe dans la réponse")
            else:
                print(f"⚠️ La clé 'failed' n'existe pas dans la réponse")
            
            # Afficher les données mises à jour
            if data.get('updated_data'):
                print(f"\n📊 Données mises à jour:")
                for item in data['updated_data']:
                    print(f"   - {item['symbol']}: {item['price']} {item['currency']}")
            
            return True
            
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Détails: {error_data}")
            except:
                print(f"   Réponse: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à {base_url}")
        print(f"   Assurez-vous que l'application Flask est démarrée")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_webapp_update_all() 