-- Script complet pour créer la base de données BONVIN Collection
-- À exécuter dans l'éditeur SQL de Supabase

-- Créer la table principale collection_items
CREATE TABLE IF NOT EXISTS collection_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Available',
    construction_year INTEGER,
    condition VARCHAR(100),
    description TEXT,
    asking_price DECIMAL(12,2),
    sold_price DECIMAL(12,2),
    acquisition_price DECIMAL(12,2),
    for_sale BOOLEAN DEFAULT FALSE,
    sale_status VARCHAR(50) DEFAULT 'initial',
    sale_progress TEXT,
    buyer_contact TEXT,
    intermediary TEXT,
    current_offer DECIMAL(12,2),
    commission_rate DECIMAL(5,2),
    last_action_date DATE,
    surface_m2 DECIMAL(8,2),
    rental_income_chf DECIMAL(12,2),
    
    -- Champs spécifiques aux actions
    stock_symbol VARCHAR(20),
    stock_quantity INTEGER,
    stock_purchase_price DECIMAL(12,2),
    stock_exchange VARCHAR(50),
    current_price DECIMAL(12,2),
    last_price_update TIMESTAMP,
    
    -- Métriques boursières supplémentaires
    stock_volume BIGINT,
    stock_pe_ratio DECIMAL(10,2),
    stock_52_week_high DECIMAL(10,2),
    stock_52_week_low DECIMAL(10,2),
    stock_change DECIMAL(10,2),
    stock_change_percent DECIMAL(10,4),
    stock_average_volume BIGINT,
    
    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536) -- Pour les embeddings OpenAI
);

-- Créer des index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_collection_items_category ON collection_items(category);
CREATE INDEX IF NOT EXISTS idx_collection_items_status ON collection_items(status);
CREATE INDEX IF NOT EXISTS idx_collection_items_for_sale ON collection_items(for_sale);
CREATE INDEX IF NOT EXISTS idx_collection_items_stock_symbol ON collection_items(stock_symbol);
CREATE INDEX IF NOT EXISTS idx_collection_items_created_at ON collection_items(created_at);

-- Créer un index pour la recherche vectorielle (si pgvector est activé)
CREATE INDEX IF NOT EXISTS idx_collection_items_embedding ON collection_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Ajouter des contraintes de validation
ALTER TABLE collection_items 
ADD CONSTRAINT chk_status CHECK (status IN ('Available', 'Sold', 'Reserved')),
ADD CONSTRAINT chk_category CHECK (category IN ('Voitures', 'Montres', 'Actions', 'Appartements / maison', 'Art', 'Vins', 'Bijoux', 'Autres')),
ADD CONSTRAINT chk_sale_status CHECK (sale_status IN ('initial', 'presentation', 'intermediary', 'inquiries', 'viewing', 'negotiation', 'offer_received', 'offer_accepted', 'paperwork', 'completed')),
ADD CONSTRAINT chk_prices CHECK (asking_price >= 0 AND sold_price >= 0 AND acquisition_price >= 0 AND current_price >= 0),
ADD CONSTRAINT chk_stock_quantity CHECK (stock_quantity > 0),
ADD CONSTRAINT chk_surface CHECK (surface_m2 > 0),
ADD CONSTRAINT chk_rental_income CHECK (rental_income_chf >= 0);

-- Ajouter des commentaires pour documenter la table
COMMENT ON TABLE collection_items IS 'Table principale pour la collection BONVIN - Inventaire complet des objets de valeur';
COMMENT ON COLUMN collection_items.name IS 'Nom de l''objet de collection';
COMMENT ON COLUMN collection_items.category IS 'Catégorie de l''objet (Voitures, Montres, Actions, etc.)';
COMMENT ON COLUMN collection_items.status IS 'Statut actuel (Available, Sold, Reserved)';
COMMENT ON COLUMN collection_items.asking_price IS 'Prix de vente demandé en CHF';
COMMENT ON COLUMN collection_items.sold_price IS 'Prix de vente final en CHF';
COMMENT ON COLUMN collection_items.acquisition_price IS 'Prix d''acquisition en CHF';
COMMENT ON COLUMN collection_items.for_sale IS 'Indique si l''objet est en vente';
COMMENT ON COLUMN collection_items.sale_status IS 'Statut de progression de la vente';
COMMENT ON COLUMN collection_items.stock_symbol IS 'Symbole boursier pour les actions';
COMMENT ON COLUMN collection_items.stock_quantity IS 'Quantité d''actions détenues';
COMMENT ON COLUMN collection_items.current_price IS 'Prix actuel de l''action en CHF';
COMMENT ON COLUMN collection_items.stock_volume IS 'Volume de transactions de l''action';
COMMENT ON COLUMN collection_items.stock_pe_ratio IS 'Ratio P/E (Price/Earnings) de l''action';
COMMENT ON COLUMN collection_items.stock_52_week_high IS 'Plus haut sur 52 semaines';
COMMENT ON COLUMN collection_items.stock_52_week_low IS 'Plus bas sur 52 semaines';
COMMENT ON COLUMN collection_items.stock_change IS 'Variation du prix (absolue)';
COMMENT ON COLUMN collection_items.stock_change_percent IS 'Variation du prix (pourcentage)';
COMMENT ON COLUMN collection_items.stock_average_volume IS 'Volume moyen sur 30 jours';
COMMENT ON COLUMN collection_items.embedding IS 'Vecteur d''embedding pour la recherche sémantique';

-- Créer une fonction pour mettre à jour automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Créer un trigger pour mettre à jour automatiquement updated_at
CREATE TRIGGER update_collection_items_updated_at 
    BEFORE UPDATE ON collection_items 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Vérifier que la table a été créée correctement
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'collection_items' 
ORDER BY ordinal_position;

-- Afficher les contraintes créées
SELECT 
    constraint_name,
    constraint_type,
    table_name
FROM information_schema.table_constraints 
WHERE table_name = 'collection_items';

-- Message de confirmation
SELECT '✅ Table collection_items créée avec succès !' as status; 