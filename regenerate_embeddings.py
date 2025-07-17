import os
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Charger les variables d'environnement du fichier .env
load_dotenv()

# Initialisation des clients
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_embedding_text(item):
    """Génère un texte riche pour l'embedding."""
    parts = [
        f"Nom: {item.get('name', '')}",
        f"Catégorie: {item.get('category', '')}",
        f"Statut: {item.get('status', '')}",
        f"Année: {item.get('construction_year', '')}",
        f"Description: {item.get('description', '')}"
    ]
    return ". ".join(filter(None, parts))

def main():
    print("Récupération de tous les objets...")
    response = supabase.table('items').select('id, name, category, status, construction_year, description').execute()
    items = response.data

    print(f"{len(items)} objets à traiter.")

    for i, item in enumerate(items):
        try:
            embedding_text = generate_embedding_text(item)
            embedding = client.embeddings.create(input=[embedding_text], model="text-embedding-3-small").data[0].embedding
            
            supabase.table('items').update({'embedding': embedding}).eq('id', item['id']).execute()
            print(f"({i+1}/{len(items)}) Embedding mis à jour pour l'objet ID {item['id']}: {item['name']}")
        except Exception as e:
            print(f"Erreur pour l'objet ID {item['id']}: {e}")

    print("Opération terminée !")

if __name__ == "__main__":
    main()
