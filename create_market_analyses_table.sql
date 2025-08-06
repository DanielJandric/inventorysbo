-- Création de la table market_analyses pour le Background Worker
CREATE TABLE IF NOT EXISTS market_analyses (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_type VARCHAR(100) NOT NULL DEFAULT 'automatic',
    summary TEXT,
    key_points JSONB,
    structured_data JSONB,
    insights JSONB,
    risks JSONB,
    opportunities JSONB,
    sources JSONB,
    confidence_score DECIMAL(3,2),
    worker_status VARCHAR(50) DEFAULT 'completed',
    processing_time_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_market_analyses_timestamp ON market_analyses(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_analyses_type ON market_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_market_analyses_status ON market_analyses(worker_status);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour mettre à jour updated_at
CREATE TRIGGER update_market_analyses_updated_at 
    BEFORE UPDATE ON market_analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insertion d'un exemple de données pour test
INSERT INTO market_analyses (
    analysis_type,
    summary,
    key_points,
    structured_data,
    insights,
    risks,
    opportunities,
    sources,
    confidence_score,
    worker_status
) VALUES (
    'automatic',
    'Analyse automatique générée par le Background Worker. Les marchés montrent une tendance positive avec un focus particulier sur l''IA.',
    '["Marchés en hausse avec focus sur l''IA", "Tendances technologiques positives", "Investissements dans l''intelligence artificielle"]',
    '{"prix": "Tendance haussière", "tendance": "Positive", "volumes": "Élevés"}',
    '["L''IA continue d''attirer les investissements"]',
    '["Volatilité possible"]',
    '["Croissance technologique"]',
    '[{"title": "Background Worker Analysis", "url": "#"}]',
    0.85,
    'completed'
) ON CONFLICT DO NOTHING; 