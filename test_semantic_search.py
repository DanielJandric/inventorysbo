import requests
import json

# URL de votre application
BASE_URL = "https://inventorysbo.onrender.com"

def test_query(query):
    """Test une requête et affiche les détails"""
    print(f"\n{'='*60}")
    print(f"🔍 Test de la requête: '{query}'")
    print('='*60)
    
    # Faire la requête
    response = requests.post(
        f"{BASE_URL}/api/chatbot",
        json={"message": query},
        timeout=30
    )
    
    if response.ok:
        data = response.json()
        
        # Afficher les métadonnées
        print("\n📊 Métadonnées:")
        metadata = data.get('metadata', {})
        for key, value in metadata.items():
            print(f"  - {key}: {value}")
        
        # Afficher le début de la réponse
        reply = data.get('reply', '')
        print("\n💬 Réponse:")
        if "🔍 **Résultats" in reply:
            print("  ❌ RECHERCHE PAR MOTS-CLÉS (fallback)")
        elif "🔍 **Recherche intelligente activée**" in reply:
            print("  ✅ RECHERCHE SÉMANTIQUE")
        else:
            print("  ❓ TYPE INCONNU")
        
        # Afficher les 500 premiers caractères
        print(f"\n{reply[:500]}...")
        
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(response.text)

def check_embeddings_status():
    """Vérifie l'état des embeddings"""
    print("\n🏥 Vérification de l'état du système...")
    
    response = requests.get(f"{BASE_URL}/health")
    if response.ok:
        data = response.json()
        embeddings = data.get('data_status', {}).get('embeddings_ready', 0)
        total = data.get('data_status', {}).get('items_count', 0)
        
        print(f"✅ Embeddings: {embeddings}/{total}")
        
        if embeddings == 0:
            print("❌ AUCUN EMBEDDING ! La recherche sémantique ne peut pas fonctionner.")
            return False
        elif embeddings < total:
            print(f"⚠️  {total - embeddings} objets sans embeddings")
        
        return True
    else:
        print("❌ Impossible de vérifier l'état")
        return False

def main():
    print("🚀 Test du système de recherche BONVIN")
    
    # Vérifier d'abord les embeddings
    if not check_embeddings_status():
        print("\n⚠️  Vous devez d'abord générer les embeddings !")
        print("Exécutez: curl -X POST https://inventorysbo.onrender.com/api/embeddings/generate")
        return
    
    # Tester différentes requêtes
    test_queries = [
        "combien j'ai de urus?",
        "combien j'ai de lamborghini?",
        "liste mes voitures",
        "montre-moi les objets en vente"
    ]
    
    for query in test_queries:
        test_query(query)
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()