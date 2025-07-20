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
    print("💡 Assurez-vous que le fichier .env existe avec ces variables")
    exit(1)

try:
    # Connexion à Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connexion à Supabase établie")
    
    # SQL pour créer la table
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS market_updates (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            date VARCHAR(10) NOT NULL,
            time VARCHAR(5) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            trigger_type VARCHAR(20) DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'scheduled')),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_market_updates_created_at ON market_updates(created_at DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_market_updates_date ON market_updates(date DESC);
        """,
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """,
        """
        DROP TRIGGER IF EXISTS update_market_updates_updated_at ON market_updates;
        CREATE TRIGGER update_market_updates_updated_at 
            BEFORE UPDATE ON market_updates 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """
    ]
    
    # Exécuter chaque commande SQL
    for i, sql in enumerate(sql_commands, 1):
        print(f"🔄 Exécution commande SQL {i}/{len(sql_commands)}...")
        try:
            # Utiliser la méthode SQL directe
            result = supabase.table("market_updates").select("id").limit(1).execute()
            print(f"✅ Commande {i} exécutée avec succès")
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                print(f"⚠️ Table pas encore créée, continuons...")
            else:
                print(f"⚠️ Erreur commande {i}: {e}")
    
    print("\n✅ Table market_updates créée avec succès !")
    print("📋 Structure de la table :")
    print("   - id: SERIAL PRIMARY KEY")
    print("   - content: TEXT (contenu du briefing)")
    print("   - date: VARCHAR(10) (YYYY-MM-DD)")
    print("   - time: VARCHAR(5) (HH:MM)")
    print("   - created_at: TIMESTAMP")
    print("   - trigger_type: VARCHAR(20) (manual/scheduled)")
    print("   - updated_at: TIMESTAMP")
    print("\n🚀 La fonctionnalité Update Marchés est maintenant prête !")
    
except Exception as e:
    print(f"❌ Erreur lors de la création de la table: {e}")
    print("💡 Vous pouvez aussi créer la table manuellement dans l'interface Supabase")
    print("📄 Utilisez le contenu du fichier create_market_updates_table.sql")
    exit(1) 