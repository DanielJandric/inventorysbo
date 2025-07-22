#!/usr/bin/env python3
"""
Test simple pour la génération de rapports de marché
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.append('.')

def test_market_briefing():
    """Test de la génération de rapports de marché"""
    
    print("🧪 Test de génération de rapports de marché")
    print("=" * 50)
    
    try:
        # Test direct de l'API Manus
        from manus_integration import generate_market_briefing_manus
        
        print("📊 Test API Manus...")
        result = generate_market_briefing_manus()
        
        print(f"   Status: {result.get('status')}")
        if result.get('status') == 'success':
            briefing = result.get('briefing', {})
            print(f"   Titre: {briefing.get('title', 'N/A')}")
            print(f"   Contenu: {len(briefing.get('content', ''))} caractères")
            print(f"   Points clés: {len(briefing.get('summary', []))} points")
            print(f"   Métriques: {len(briefing.get('metrics', {}))} métriques")
            
            # Afficher un extrait du contenu
            content = briefing.get('content', '')
            if content:
                print(f"\n📝 Extrait du contenu (premiers 200 caractères):")
                print(f"   {content[:200]}...")
        else:
            print(f"   Erreur: {result.get('message', 'Erreur inconnue')}")
        
        print("\n✅ Test terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    test_market_briefing() 