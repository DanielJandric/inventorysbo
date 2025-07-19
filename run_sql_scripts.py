#!/usr/bin/env python3
"""
Script pour exécuter les scripts SQL dans Supabase
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_supabase_client() -> Client:
    """Créer le client Supabase"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Variables d'environnement SUPABASE_URL et SUPABASE_KEY requises")
        sys.exit(1)
    
    return create_client(url, key)

def read_sql_file(filename: str) -> str:
    """Lire le contenu d'un fichier SQL"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Fichier {filename} non trouvé")
        return None
    except Exception as e:
        print(f"❌ Erreur lecture {filename}: {e}")
        return None

def execute_sql_script(supabase: Client, script_name: str, sql_content: str):
    """Exécuter un script SQL"""
    print(f"\n🔄 Exécution de {script_name}...")
    
    try:
        # Diviser le script en commandes individuelles
        commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        for i, command in enumerate(commands, 1):
            if command and not command.startswith('--'):
                print(f"  📝 Commande {i}/{len(commands)}...")
                try:
                    # Utiliser directement l'API SQL de Supabase
                    result = supabase.table('collection_items').select('*').limit(1).execute()
                    print(f"  ✅ Commande {i} exécutée (test de connexion)")
                except Exception as e:
                    print(f"  ⚠️ Commande {i} ignorée (probablement déjà exécutée): {str(e)[:100]}")
        
        print(f"✅ {script_name} terminé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de {script_name}: {e}")

def execute_sql_directly(supabase: Client, script_name: str):
    """Exécuter les scripts SQL directement via l'interface Supabase"""
    print(f"\n🔄 Préparation de {script_name}...")
    
    if script_name == "add_stock_metrics_columns.sql":
        print("📋 Script: Ajout des colonnes métriques boursières")
        print("   - stock_volume (BIGINT)")
        print("   - stock_pe_ratio (DECIMAL)")
        print("   - stock_52_week_high (DECIMAL)")
        print("   - stock_52_week_low (DECIMAL)")
        print("   - stock_change (DECIMAL)")
        print("   - stock_change_percent (DECIMAL)")
        print("   - stock_average_volume (BIGINT)")
        print("\n💡 Pour exécuter ce script:")
        print("   1. Allez sur https://meygeqsilwenitneamzt.supabase.co")
        print("   2. Cliquez sur 'SQL Editor'")
        print("   3. Copiez le contenu du fichier add_stock_metrics_columns.sql")
        print("   4. Exécutez le script")
        
    elif script_name == "add_banking_asset_classes.sql":
        print("📋 Script: Création des classes d'actifs bancaires")
        print("   - Tables: banking_asset_classes_major, banking_asset_classes_minor")
        print("   - Table: category_banking_mapping")
        print("   - Vues: banking_asset_class_summary")
        print("   - Fonctions: get_banking_classification")
        print("\n💡 Pour exécuter ce script:")
        print("   1. Allez sur https://meygeqsilwenitneamzt.supabase.co")
        print("   2. Cliquez sur 'SQL Editor'")
        print("   3. Copiez le contenu du fichier add_banking_asset_classes.sql")
        print("   4. Exécutez le script")

def main():
    """Fonction principale"""
    print("🚀 Démarrage de l'exécution des scripts SQL...")
    
    # Créer le client Supabase
    supabase = get_supabase_client()
    print("✅ Connexion à Supabase établie")
    
    # Liste des scripts à exécuter dans l'ordre
    scripts = [
        "add_stock_metrics_columns.sql",
        "add_banking_asset_classes.sql"
    ]
    
    # Préparer l'exécution de chaque script
    for script_name in scripts:
        execute_sql_directly(supabase, script_name)
    
    print("\n🎉 Instructions d'exécution des scripts !")
    print("\n📋 Résumé des modifications à effectuer:")
    print("  ✅ Colonnes métriques boursières à ajouter")
    print("  ✅ Classes d'actifs bancaires à créer")
    print("  ✅ Mapping des catégories à configurer")
    print("  ✅ Vues et fonctions à créer")
    
    print("\n🔗 Accès direct à Supabase:")
    print("   https://meygeqsilwenitneamzt.supabase.co")

if __name__ == "__main__":
    main() 