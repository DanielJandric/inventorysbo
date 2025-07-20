-- Création de la table market_updates pour les briefings de marché
CREATE TABLE IF NOT EXISTS market_updates (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    date VARCHAR(10) NOT NULL,
    time VARCHAR(5) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trigger_type VARCHAR(20) DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'scheduled')),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_market_updates_created_at ON market_updates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_updates_date ON market_updates(date DESC);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_market_updates_updated_at 
    BEFORE UPDATE ON market_updates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Commentaires pour la documentation
COMMENT ON TABLE market_updates IS 'Table pour stocker les briefings de marché générés automatiquement ou manuellement';
COMMENT ON COLUMN market_updates.content IS 'Contenu du briefing de marché généré par GPT-4o';
COMMENT ON COLUMN market_updates.date IS 'Date du briefing au format YYYY-MM-DD';
COMMENT ON COLUMN market_updates.time IS 'Heure de génération au format HH:MM';
COMMENT ON COLUMN market_updates.trigger_type IS 'Type de déclenchement: manual ou scheduled'; 