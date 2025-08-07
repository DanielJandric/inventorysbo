-- Création de la table pour les annonces immobilières
CREATE TABLE IF NOT EXISTS real_estate_listings (
    id SERIAL PRIMARY KEY,
    source_url TEXT UNIQUE NOT NULL, -- URL de l'annonce originale, contrainte d'unicité pour éviter les doublons
    source_site VARCHAR(100), -- Ex: 'immoscout24.ch'
    title TEXT,
    location TEXT,
    price BIGINT,
    rental_income_yearly BIGINT,
    yield_percentage DECIMAL(4,2),
    number_of_apartments INT,
    living_space_m2 INT,
    plot_surface_m2 INT,
    image_url TEXT,
    description_summary TEXT,
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'contacted', 'archived'
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_real_estate_status ON real_estate_listings(status);
CREATE INDEX IF NOT EXISTS idx_real_estate_location ON real_estate_listings(location);
CREATE INDEX IF NOT EXISTS idx_real_estate_price ON real_estate_listings(price);

-- Trigger pour mettre à jour updated_at automatiquement (si la fonction existe déjà, cela ne fera rien)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_real_estate_listings_updated_at
    BEFORE UPDATE ON real_estate_listings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
