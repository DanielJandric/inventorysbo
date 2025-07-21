-- Création de la table pour les briefings de marché
CREATE TABLE IF NOT EXISTS market_updates (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    date VARCHAR(10) NOT NULL,
    time VARCHAR(5) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trigger_type VARCHAR(20) DEFAULT 'manual',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_market_updates_date ON market_updates(date);
CREATE INDEX IF NOT EXISTS idx_market_updates_created_at ON market_updates(created_at);

-- Commentaires sur la table et les colonnes
COMMENT ON TABLE market_updates IS 'Table pour stocker les briefings de marché générés automatiquement ou manuellement';
COMMENT ON COLUMN market_updates.id IS 'Identifiant unique du briefing';
COMMENT ON COLUMN market_updates.content IS 'Contenu du briefing de marché généré par Gemini 1.5 Flash avec recherche web';
COMMENT ON COLUMN market_updates.date IS 'Date du briefing au format YYYY-MM-DD';
COMMENT ON COLUMN market_updates.time IS 'Heure de génération au format HH:MM';
COMMENT ON COLUMN market_updates.created_at IS 'Timestamp de création du briefing';
COMMENT ON COLUMN market_updates.trigger_type IS 'Type de déclenchement: manual ou scheduled';
COMMENT ON COLUMN market_updates.updated_at IS 'Timestamp de dernière modification';

-- Contrainte pour s'assurer que la date est au bon format
ALTER TABLE market_updates ADD CONSTRAINT check_date_format 
CHECK (date ~ '^\d{4}-\d{2}-\d{2}$');

-- Contrainte pour s'assurer que l'heure est au bon format
ALTER TABLE market_updates ADD CONSTRAINT check_time_format 
CHECK (time ~ '^\d{2}:\d{2}$');

-- Contrainte pour s'assurer que trigger_type est valide
ALTER TABLE market_updates ADD CONSTRAINT check_trigger_type 
CHECK (trigger_type IN ('manual', 'scheduled'));

-- RLS (Row Level Security) - Désactivé par défaut pour permettre l'accès
ALTER TABLE market_updates ENABLE ROW LEVEL SECURITY;

-- Politique pour permettre l'accès public (à ajuster selon vos besoins)
CREATE POLICY "Allow public access to market_updates" ON market_updates
    FOR ALL USING (true);

-- Insertion d'un exemple de briefing (optionnel)
-- INSERT INTO market_updates (content, date, time, trigger_type) VALUES (
--     'Exemple de briefing de marché généré par Gemini avec recherche web...',
--     CURRENT_DATE,
--     TO_CHAR(CURRENT_TIME, 'HH24:MI'),
--     'manual'
-- ); 