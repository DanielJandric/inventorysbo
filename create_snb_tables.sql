-- =====================================================
-- TABLES POUR LE MODÈLE SNB POLICY ENGINE
-- À exécuter dans Supabase SQL Editor
-- =====================================================

-- Table 1: Données CPI (Inflation OFS)
CREATE TABLE IF NOT EXISTS snb_cpi_data (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL DEFAULT 'BFS',
    as_of DATE NOT NULL,
    yoy_pct NUMERIC(10, 4) NOT NULL,
    mm_pct NUMERIC(10, 4),
    source_url TEXT,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 2: Données KOF (Baromètre économique)
CREATE TABLE IF NOT EXISTS snb_kof_data (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL DEFAULT 'KOF',
    as_of DATE NOT NULL,
    barometer NUMERIC(10, 2) NOT NULL,
    source_url TEXT,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 3: Prévisions SNB (communiqués MPA)
CREATE TABLE IF NOT EXISTS snb_forecasts (
    id SERIAL PRIMARY KEY,
    meeting_date DATE NOT NULL UNIQUE,
    forecast JSONB NOT NULL, -- {"2025": 0.2, "2026": 0.5, "2027": 0.7}
    source_url TEXT,
    pdf_url TEXT,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 4: Courbe OIS / Futures SARON
CREATE TABLE IF NOT EXISTS snb_ois_data (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL UNIQUE,
    points JSONB NOT NULL, -- [{"tenor_months": 3, "rate_pct": 0.00}, ...]
    source_url TEXT,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 5: Résultats du modèle (runs)
CREATE TABLE IF NOT EXISTS snb_model_runs (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    inputs JSONB NOT NULL,
    nowcast JSONB NOT NULL,
    output_gap_pct NUMERIC(10, 4) NOT NULL,
    i_star_next_pct NUMERIC(10, 4) NOT NULL,
    probs JSONB NOT NULL, -- {"cut": 0.076, "hold": 0.848, "hike": 0.076}
    path JSONB NOT NULL, -- [{month_ahead, rule, market, fused, var}, ...]
    version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_snb_cpi_as_of ON snb_cpi_data(as_of DESC);
CREATE INDEX IF NOT EXISTS idx_snb_kof_as_of ON snb_kof_data(as_of DESC);
CREATE INDEX IF NOT EXISTS idx_snb_forecasts_meeting_date ON snb_forecasts(meeting_date DESC);
CREATE INDEX IF NOT EXISTS idx_snb_ois_as_of ON snb_ois_data(as_of DESC);
CREATE INDEX IF NOT EXISTS idx_snb_model_runs_as_of ON snb_model_runs(as_of DESC);

-- Enable Row Level Security (RLS) - à adapter selon vos besoins
ALTER TABLE snb_cpi_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE snb_kof_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE snb_forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE snb_ois_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE snb_model_runs ENABLE ROW LEVEL SECURITY;

-- Politique RLS (exemple: accès authentifié)
-- À ADAPTER selon votre configuration auth Supabase
CREATE POLICY "Allow authenticated read access" ON snb_cpi_data FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read access" ON snb_kof_data FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read access" ON snb_forecasts FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read access" ON snb_ois_data FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated read access" ON snb_model_runs FOR SELECT USING (auth.role() = 'authenticated');

-- Si vous voulez permettre l'insertion depuis le backend (service_role key)
-- CREATE POLICY "Allow service role insert" ON snb_cpi_data FOR INSERT WITH CHECK (true);
-- (répéter pour les autres tables si nécessaire)

-- Table de configuration (pour stocker le taux directeur actuel et NEER)
CREATE TABLE IF NOT EXISTS snb_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Taux directeur BNS actuel (MPA 25 septembre 2025)
INSERT INTO snb_config (key, value) VALUES ('policy_rate_now_pct', '0.0'::jsonb)
ON CONFLICT (key) DO UPDATE SET value = '0.0'::jsonb, updated_at = NOW();

