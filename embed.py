import os
import openai
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement
load_dotenv()

print("Initialisation des clients...")
# Configuration des clients
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_api_key]):
        raise ValueError("Erreur: Assurez-vous que SUPABASE_URL, SUPABASE_KEY, et OPENAI_API_KEY sont définis.")

    supabase: Client = create_client(supabase_url, supabase_key)
    client = openai.OpenAI(api_key=openai_api_key)
    print("Clients initialisés avec succès.")
except Exception as e:
    print(f"Erreur d'initialisation: {e}")
    exit()

def generate_embedding(text):
    """Génère un embedding pour un texte donné."""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def main():
    """Script principal pour générer et sauvegarder les embeddings."""
    print("Récupération des objets sans embedding depuis Supabase...")
    # On ne récupère que les objets qui n'ont pas encore d'embedding pour être plus efficace
    response = supabase.table('items').select('id, name, category, description, status').filter('embedding', 'is', 'null').execute()
    items = response.data
    
    if not items:
        print("Aucun nouvel objet à traiter. L'inventaire est déjà à jour.")
        return

    print(f"{len(items)} objets à traiter. Début de la génération des embeddings...")
    
    for item in items:
        try:
            # Créer un texte descriptif pour chaque objet
            content_to_embed = (
                f"Nom: {item.get('name', '')}. "
                f"Catégorie: {item.get('category', '')}. "
                f"Statut: {item.get('status', '')}. "
                f"Description: {item.get('description', '')}"
            )
            
            print(f"Génération de l'embedding pour l'objet ID {item['id']}: {item['name']}...")
            
            # Générer l'embedding
            embedding = generate_embedding(content_to_embed)
            
            # Sauvegarder l'embedding dans Supabase
            supabase.table('items').update({'embedding': embedding}).eq('id', item['id']).execute()
            print(f" -> Succès pour l'ID {item['id']}.")

        except Exception as e:
            print(f" -> ERREUR pour l'ID {item['id']}: {e}")

    print("\nOpération terminée !")

if __name__ == "__main__":
    main()
