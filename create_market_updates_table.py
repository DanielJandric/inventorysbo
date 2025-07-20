#!/usr/bin/env python3
"""
Script pour créer la table market_updates dans Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Charger les variables d'environnement
load_dotenv()

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Variables d'environnement SUPABASE_URL et SUPABASE_KEY requises")
    exit(1)

try:
    # Connexion à Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connexion à Supabase établie")
    
    # Lire le fichier SQL
    with open('create_market_updates_table.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Exécuter le SQL
    print("🔄 Création de la table market_updates...")
    result = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
    
    print("✅ Table market_updates créée avec succès !")
    print("📋 Structure de la table :")
    print("   - id: SERIAL PRIMARY KEY")
    print("   - content: TEXT (contenu du briefing)")
    print("   - date: VARCHAR(10) (YYYY-MM-DD)")
    print("   - time: VARCHAR(5) (HH:MM)")
    print("   - created_at: TIMESTAMP")
    print("   - trigger_type: VARCHAR(20) (manual/scheduled)")
    print("   - updated_at: TIMESTAMP")
    
except Exception as e:
    print(f"❌ Erreur lors de la création de la table: {e}")
    exit(1) 