import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
from typing import List, Dict, Optional, Tuple

# --- CONFIGURATION ET CONSTANTES ---
BATCH_SIZE = 10  # Nombre d'objets à traiter avant une pause
RATE_LIMIT_PAUSE = 1  # Pause en secondes entre les batches
MAX_RETRIES = 3  # Nombre de tentatives en cas d'erreur
RETRY_DELAY = 2  # Délai entre les tentatives

# --- CHEMIN EXPLICITE VERS LE FICHIER .ENV ---
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(dotenv_path):
    print("❌ ERREUR CRITIQUE: Fichier .env introuvable. Veuillez le créer à la racine du projet.")
    sys.exit(1)

# Charger les variables d'environnement
load_dotenv(dotenv_path=dotenv_path)

# --- VÉRIFICATION DES VARIABLES D'ENVIRONNEMENT ---
required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
missing_vars = []

for var in required_vars:
    if not os.environ.get(var):
        missing_vars.append(var)

if missing_vars:
    print(f"❌ ERREUR CRITIQUE: Variables manquantes: {', '.join(missing_vars)}")
    print("Veuillez les ajouter dans votre fichier .env")
    sys.exit(1)

# --- INITIALISATION DES CLIENTS ---
try:
    supabase: Client = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    print("✅ Clients initialisés avec succès")
except Exception as e:
    print(f"❌ Erreur d'initialisation des clients: {e}")
    sys.exit(1)

# --- STATISTIQUES GLOBALES ---
class Stats:
    def __init__(self):
        self.total_items = 0
        self.items_with_embedding = 0
        self.items_without_embedding = 0
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.start_time = None
        self.errors_log = []

stats = Stats()

def generate_embedding_text(item: Dict) -> str:
    """Génère un texte riche et descriptif pour l'embedding."""
    parts = []
    
    # Nom et catégorie (toujours inclus)
    parts.append(f"Nom: {item.get('name', 'Sans nom')}")
    parts.append(f"Catégorie: {item.get('category', 'Non catégorisé')}")
    
    # Statut avec détails
    if item.get('for_sale'):
        parts.append("Statut: En vente actuellement")
        if item.get('sale_status'):
            sale_status_labels = {
                'initial': 'Mise en vente initiale',
                'presentation': 'En préparation de présentation',
                'intermediary': 'Recherche d\'intermédiaires',
                'inquiries': 'Premières demandes reçues',
                'viewing': 'Visites programmées',
                'negotiation': 'En négociation active',
                'offer_received': 'Offre reçue',
                'offer_accepted': 'Offre acceptée',
                'paperwork': 'Formalités en cours',
                'completed': 'Vente finalisée'
            }
            status_label = sale_status_labels.get(item.get('sale_status'), item.get('sale_status'))
            parts.append(f"Progression de vente: {status_label}")
    else:
        status = "Disponible" if item.get('status') == 'Available' else "Vendu"
        parts.append(f"Statut: {status}")
    
    # Année et condition
    if item.get('construction_year'):
        parts.append(f"Année: {item['construction_year']}")
        age = datetime.now().year - item['construction_year']
        if age <= 2:
            parts.append("Objet très récent")
        elif age <= 5:
            parts.append("Objet récent")
        elif age >= 20:
            parts.append("Objet vintage ou de collection")
    
    if item.get('condition'):
        parts.append(f"État: {item['condition']}")
    
    # Prix et valeur
    if item.get('status') == 'Available' and item.get('current_value'):
        parts.append(f"valeur actuelle: {item['current_value']:,.0f} CHF")
        if item.get('current_offer'):
            parts.append(f"Offre actuelle: {item['current_offer']:,.0f} CHF")
    elif item.get('sold_price'):
        parts.append(f"Vendu pour: {item['sold_price']:,.0f} CHF")
    
    # Informations spécifiques selon la catégorie
    if item.get('category') == 'Appartements / maison':
        if item.get('surface_m2'):
            parts.append(f"Surface: {item['surface_m2']} m²")
        if item.get('rental_income_chf'):
            parts.append(f"Revenus locatifs: {item['rental_income_chf']:,.0f} CHF/mois")
    
    # Description (toujours à la fin pour plus de contexte)
    if item.get('description'):
        parts.append(f"Description: {item['description']}")
    
    # Informations de vente additionnelles
    if item.get('sale_progress'):
        parts.append(f"Détails de progression: {item['sale_progress']}")
    
    if item.get('intermediary'):
        parts.append(f"Intermédiaire: {item['intermediary']}")
    
    return ". ".join(filter(None, parts))

def generate_embedding_with_retry(text: str, item_id: int, max_retries: int = MAX_RETRIES) -> Optional[List[float]]:
    """Génère un embedding avec gestion des erreurs et retry."""
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"\n⚠️  Tentative {attempt + 1}/{max_retries} échouée pour ID {item_id}: {str(e)[:50]}...")
                time.sleep(RETRY_DELAY * (attempt + 1))  # Délai progressif
            else:
                print(f"\n❌ Échec définitif pour ID {item_id} après {max_retries} tentatives")
                stats.errors_log.append({
                    'item_id': item_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                return None

def update_embedding_in_supabase(item_id: int, embedding: List[float]) -> bool:
    """Met à jour l'embedding dans Supabase avec gestion d'erreur."""
    try:
        response = supabase.table('items').update({
            'embedding': embedding,
            'updated_at': datetime.now().isoformat()
        }).eq('id', item_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"\n❌ Erreur sauvegarde Supabase pour ID {item_id}: {e}")
        stats.errors_log.append({
            'item_id': item_id,
            'error': f"Supabase error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        })
        return False

def display_progress(current: int, total: int, item_name: str):
    """Affiche une barre de progression."""
    progress = current / total * 100
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Calculer le temps écoulé et estimer le temps restant
    if stats.start_time:
        elapsed = time.time() - stats.start_time
        if current > 0:
            estimated_total = elapsed * total / current
            remaining = estimated_total - elapsed
            time_info = f" | ⏱️  {format_time(elapsed)} / ~{format_time(remaining)}"
        else:
            time_info = ""
    else:
        time_info = ""
    
    # Tronquer le nom si trop long
    display_name = item_name[:30] + "..." if len(item_name) > 30 else item_name
    
    print(f"\r[{bar}] {progress:5.1f}% ({current}/{total}) - {display_name}{time_info}", end='', flush=True)

def format_time(seconds: float) -> str:
    """Formate le temps en format lisible."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds//60:.0f}m {seconds%60:.0f}s"
    else:
        return f"{seconds//3600:.0f}h {(seconds%3600)//60:.0f}m"

def save_error_log():
    """Sauvegarde le log des erreurs dans un fichier."""
    if stats.errors_log:
        filename = f"embedding_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats.errors_log, f, indent=2, ensure_ascii=False)
        print(f"\n📝 Log des erreurs sauvegardé dans: {filename}")

def main():
    """Script principal pour générer et sauvegarder les embeddings."""
    print("\n🚀 BONVIN Collection - Génération des Embeddings")
    print("=" * 60)
    
    # Récupération de tous les objets
    print("📦 Récupération des objets depuis Supabase...")
    try:
        response = supabase.table('items').select('*').order('id').execute()
        all_items = response.data
        stats.total_items = len(all_items)
        print(f"✅ {stats.total_items} objets récupérés")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        sys.exit(1)
    
    if not all_items:
        print("ℹ️  Aucun objet dans la base de données.")
        return
    
    # Analyse des embeddings existants
    print("\n📊 Analyse des embeddings existants...")
    items_to_process = []
    
    for item in all_items:
        if item.get('embedding') and len(item['embedding']) > 0:
            stats.items_with_embedding += 1
        else:
            items_to_process.append(item)
            stats.items_without_embedding += 1
    
    print(f"  ✅ Avec embedding: {stats.items_with_embedding}")
    print(f"  ❌ Sans embedding: {stats.items_without_embedding}")
    
    if not items_to_process:
        print("\n✅ Tous les objets ont déjà un embedding!")
        return
    
    # Options utilisateur
    print(f"\n🔧 Options:")
    print(f"  1. Générer les embeddings manquants ({stats.items_without_embedding} objets)")
    print(f"  2. Régénérer TOUS les embeddings ({stats.total_items} objets)")
    print(f"  3. Quitter")
    
    choice = input("\nVotre choix (1/2/3): ").strip()
    
    if choice == '3':
        print("👋 Opération annulée")
        return
    elif choice == '2':
        if input(f"\n⚠️  Êtes-vous sûr de vouloir régénérer TOUS les {stats.total_items} embeddings? (oui/non): ").lower() != 'oui':
            print("👋 Opération annulée")
            return
        items_to_process = all_items
        stats.items_without_embedding = stats.total_items
    elif choice != '1':
        print("❌ Choix invalide")
        return
    
    # Estimation du coût
    estimated_tokens = sum(len(generate_embedding_text(item).split()) * 1.3 for item in items_to_process)
    estimated_cost = (estimated_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens
    
    print(f"\n💰 Estimation du coût:")
    print(f"  - Tokens estimés: ~{estimated_tokens:,.0f}")
    print(f"  - Coût estimé: ~${estimated_cost:.3f}")
    
    if input("\nContinuer? (oui/non): ").lower() != 'oui':
        print("👋 Opération annulée")
        return
    
    # Génération des embeddings
    print(f"\n🔄 Génération de {len(items_to_process)} embeddings...")
    print("=" * 60)
    stats.start_time = time.time()
    
    for i, item in enumerate(items_to_process):
        try:
            # Afficher la progression
            display_progress(i + 1, len(items_to_process), item.get('name', 'Sans nom'))
            
            # Générer le texte et l'embedding
            embedding_text = generate_embedding_text(item)
            embedding = generate_embedding_with_retry(embedding_text, item['id'])
            
            if embedding:
                # Sauvegarder dans Supabase
                if update_embedding_in_supabase(item['id'], embedding):
                    stats.success_count += 1
                else:
                    stats.error_count += 1
            else:
                stats.error_count += 1
            
            # Pause pour éviter le rate limiting
            if (i + 1) % BATCH_SIZE == 0 and i < len(items_to_process) - 1:
                print(f"\n⏸️  Pause de {RATE_LIMIT_PAUSE}s (rate limiting)...")
                time.sleep(RATE_LIMIT_PAUSE)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption par l'utilisateur")
            break
        except Exception as e:
            stats.error_count += 1
            print(f"\n❌ Erreur inattendue pour {item.get('name', 'ID ' + str(item['id']))}: {e}")
            stats.errors_log.append({
                'item_id': item['id'],
                'item_name': item.get('name', 'Sans nom'),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    # Résumé final
    elapsed_time = time.time() - stats.start_time
    print("\n\n" + "=" * 60)
    print("📊 RÉSUMÉ DE L'OPÉRATION")
    print("=" * 60)
    print(f"⏱️  Durée totale: {format_time(elapsed_time)}")
    print(f"✅ Succès: {stats.success_count}")
    print(f"❌ Erreurs: {stats.error_count}")
    print(f"⏭️  Ignorés: {stats.skipped_count}")
    print(f"📈 Taux de réussite: {stats.success_count / len(items_to_process) * 100:.1f}%")
    
    if stats.success_count > 0:
        print(f"⚡ Vitesse moyenne: {elapsed_time / stats.success_count:.2f}s/objet")
    
    # Sauvegarder le log des erreurs si nécessaire
    if stats.errors_log:
        save_error_log()
    
    # Vérification finale
    print("\n🔍 Vérification finale...")
    try:
        response = supabase.table('items').select('id, embedding').execute()
        final_items = response.data
        final_with_embedding = len([item for item in final_items if item.get('embedding')])
        print(f"✅ Total objets avec embedding: {final_with_embedding}/{len(final_items)}")
    except Exception as e:
        print(f"⚠️  Impossible de vérifier: {e}")
    
    print("\n✨ Opération terminée!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Opération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()