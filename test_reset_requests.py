#!/usr/bin/env python3
"""
Script de test pour la réinitialisation du compteur de requêtes Yahoo Finance
"""

import requests
import json
import time

def test_reset_requests():
    """Test de la réinitialisation du compteur de requêtes"""
    
    base_url = "http://localhost:5000"  # Ajuster selon votre configuration
    
    print("🧪 Test de réinitialisation du compteur de requêtes")
    print("=" * 60)
    
    # 1. Vérifier le statut initial
    print("\n1️⃣ Vérification du statut initial...")
    try:
        response = requests.get(f"{base_url}/api/stock-price/cache/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statut initial récupéré")
            print(f"   Requêtes utilisées: {data.get('daily_requests', 'N/A')}")
            print(f"   Limite maximale: {data.get('max_daily_requests', 'N/A')}")
            print(f"   Peut faire des requêtes: {data.get('can_make_request', 'N/A')}")
        else:
            print(f"❌ Erreur récupération statut: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return
    
    # 2. Réinitialiser le compteur
    print("\n2️⃣ Réinitialisation du compteur...")
    try:
        response = requests.post(f"{base_url}/api/stock-price/reset-requests")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f"✅ Compteur réinitialisé avec succès")
                print(f"   Nouveau compteur: {data.get('requests', 'N/A')}")
                print(f"   Date: {data.get('date', 'N/A')}")
            else:
                print(f"❌ Erreur réinitialisation: {data.get('message', 'Erreur inconnue')}")
                return
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return
    
    # 3. Vérifier le statut après réinitialisation
    print("\n3️⃣ Vérification du statut après réinitialisation...")
    try:
        response = requests.get(f"{base_url}/api/stock-price/cache/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statut après réinitialisation récupéré")
            print(f"   Requêtes utilisées: {data.get('daily_requests', 'N/A')}")
            print(f"   Limite maximale: {data.get('max_daily_requests', 'N/A')}")
            print(f"   Peut faire des requêtes: {data.get('can_make_request', 'N/A')}")
            
            # Vérifier que le compteur a été réinitialisé
            if data.get('daily_requests') == 0:
                print("✅ Compteur correctement réinitialisé à 0")
            else:
                print(f"⚠️ Compteur non réinitialisé: {data.get('daily_requests')}")
        else:
            print(f"❌ Erreur récupération statut: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
    
    # 4. Test d'une requête API
    print("\n4️⃣ Test d'une requête API après réinitialisation...")
    try:
        response = requests.post(f"{base_url}/api/stock-price/update-all")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Requête API réussie après réinitialisation")
                print(f"   Symboles traités: {data.get('updated_count', 'N/A')}")
                print(f"   Requêtes utilisées: {data.get('requests_used', 'N/A')}")
            else:
                print(f"❌ Erreur requête API: {data.get('error', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur API: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_reset_requests() 