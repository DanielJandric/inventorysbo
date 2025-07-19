-- Script pour ajouter les classes d'actifs bancaires dans Supabase
-- Exécuter ce script dans l'éditeur SQL de Supabase

-- 1. Créer la table des classes d'actifs majeures
CREATE TABLE IF NOT EXISTS banking_asset_classes_major (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Créer la table des sous-classes d'actifs
CREATE TABLE IF NOT EXISTS banking_asset_classes_minor (
    id SERIAL PRIMARY KEY,
    major_class_id INTEGER REFERENCES banking_asset_classes_major(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(major_class_id, name)
);

-- 3. Créer la table de mapping entre les catégories existantes et les classes bancaires
CREATE TABLE IF NOT EXISTS category_banking_mapping (
    id SERIAL PRIMARY KEY,
    original_category VARCHAR(100) NOT NULL UNIQUE,
    major_class_id INTEGER REFERENCES banking_asset_classes_major(id) ON DELETE CASCADE,
    minor_class_id INTEGER REFERENCES banking_asset_classes_minor(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Insérer les classes d'actifs majeures selon la terminologie bancaire
INSERT INTO banking_asset_classes_major (name, description) VALUES
('Titres cotés en bourse', 'Actions cotées sur les marchés financiers'),
('Actifs réels', 'Véhicules de collection et de luxe'),
('Immobilier direct ou indirect', 'Biens immobiliers résidentiels, commerciaux et de rendement'),
('Private Equity / Venture Capital', 'Start-ups et participations dans des entreprises non cotées')
ON CONFLICT (name) DO NOTHING;

-- 5. Insérer les sous-classes d'actifs selon la terminologie bancaire
-- Titres cotés en bourse
INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Actions', 'Actions cotées sur les marchés financiers'
FROM banking_asset_classes_major WHERE name = 'Titres cotés en bourse'
ON CONFLICT (major_class_id, name) DO NOTHING;

-- Actifs réels
INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Automobiles', 'Véhicules de collection ou de luxe'
FROM banking_asset_classes_major WHERE name = 'Actifs réels'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Bateaux', 'Yachts, bateaux de plaisance'
FROM banking_asset_classes_major WHERE name = 'Actifs réels'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Avions', 'Jets privés, aviation d''affaires'
FROM banking_asset_classes_major WHERE name = 'Actifs réels'
ON CONFLICT (major_class_id, name) DO NOTHING;

-- Immobilier direct ou indirect
INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Immobilier résidentiel', 'Logements'
FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Immobilier de rendement', 'Biens générant des revenus locatifs'
FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Immobilier hôtelier', 'Complexes resort touristiques, hôtels'
FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Projets immobiliers', 'Projets de développement immobilier'
FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'
ON CONFLICT (major_class_id, name) DO NOTHING;

-- Private Equity / Venture Capital
INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Start-ups', 'Jeunes entreprises non cotées'
FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Sociétés de rénovation', 'Services immobiliers'
FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'
ON CONFLICT (major_class_id, name) DO NOTHING;

INSERT INTO banking_asset_classes_minor (major_class_id, name, description) 
SELECT id, 'Sociétés de e-commerce', 'Participations non cotées dans le e-commerce'
FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'
ON CONFLICT (major_class_id, name) DO NOTHING;

-- 6. Créer le mapping entre les catégories existantes et les classes bancaires
INSERT INTO category_banking_mapping (original_category, major_class_id, minor_class_id) VALUES
-- Titres cotés en bourse
('Actions', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Titres cotés en bourse'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Actions' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Titres cotés en bourse'))
),

-- Actifs réels
('Voitures', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Actifs réels'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Automobiles' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Actifs réels'))
),

('Bateaux', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Actifs réels'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Bateaux' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Actifs réels'))
),

('Avions', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Actifs réels'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Avions' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Actifs réels'))
),

-- Immobilier direct ou indirect
('Appartements / maison', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier résidentiel' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Be Capital', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier de rendement' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Saanen', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Projets immobiliers' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Dixence Resort', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier hôtelier' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Investis properties', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier de rendement' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Mibo', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier de rendement' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Portfolio Rhône Hotels', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier hôtelier' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('Rhône Property – Portfolio IAM', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier de rendement' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

('IB', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Immobilier résidentiel' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Immobilier direct ou indirect'))
),

-- Private Equity / Venture Capital
('Start ups', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Start-ups' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'))
),

('Investis services', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Sociétés de rénovation' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'))
),

('Be Capital Activities', 
 (SELECT id FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'),
 (SELECT id FROM banking_asset_classes_minor WHERE name = 'Sociétés de e-commerce' AND major_class_id = (SELECT id FROM banking_asset_classes_major WHERE name = 'Private Equity / Venture Capital'))
)
ON CONFLICT (original_category) DO NOTHING;

-- 7. Créer des vues utiles pour les rapports
CREATE OR REPLACE VIEW banking_asset_class_summary AS
SELECT 
    mac.name as major_class,
    macm.name as minor_class,
    COUNT(i.id) as item_count,
    SUM(COALESCE(i.acquisition_price, 0)) as total_acquisition_value,
    SUM(COALESCE(i.current_price * i.stock_quantity, i.acquisition_price, 0)) as total_current_value,
    AVG(COALESCE(i.acquisition_price, 0)) as avg_acquisition_price
FROM banking_asset_classes_major mac
JOIN banking_asset_classes_minor macm ON mac.id = macm.major_class_id
LEFT JOIN category_banking_mapping cbm ON macm.id = cbm.minor_class_id
LEFT JOIN items i ON cbm.original_category = i.category
WHERE i.status != 'Sold' OR i.status IS NULL
GROUP BY mac.id, mac.name, macm.id, macm.name
ORDER BY mac.name, macm.name;

-- 8. Créer une fonction pour obtenir la classification bancaire d'un item
CREATE OR REPLACE FUNCTION get_banking_classification(category_name VARCHAR)
RETURNS TABLE(
    major_class VARCHAR,
    minor_class VARCHAR,
    major_description TEXT,
    minor_description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mac.name as major_class,
        macm.name as minor_class,
        mac.description as major_description,
        macm.description as minor_description
    FROM category_banking_mapping cbm
    JOIN banking_asset_classes_major mac ON cbm.major_class_id = mac.id
    JOIN banking_asset_classes_minor macm ON cbm.minor_class_id = macm.id
    WHERE cbm.original_category = category_name;
END;
$$ LANGUAGE plpgsql;

-- 9. Ajouter des index pour les performances
CREATE INDEX IF NOT EXISTS idx_category_banking_mapping_original ON category_banking_mapping(original_category);
CREATE INDEX IF NOT EXISTS idx_banking_asset_classes_major_name ON banking_asset_classes_major(name);
CREATE INDEX IF NOT EXISTS idx_banking_asset_classes_minor_major_id ON banking_asset_classes_minor(major_class_id);

-- 10. Créer des triggers pour maintenir updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Supprimer les triggers existants s'ils existent
DROP TRIGGER IF EXISTS update_banking_asset_classes_major_updated_at ON banking_asset_classes_major;
DROP TRIGGER IF EXISTS update_banking_asset_classes_minor_updated_at ON banking_asset_classes_minor;
DROP TRIGGER IF EXISTS update_category_banking_mapping_updated_at ON category_banking_mapping;

-- Créer les triggers
CREATE TRIGGER update_banking_asset_classes_major_updated_at 
    BEFORE UPDATE ON banking_asset_classes_major 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_banking_asset_classes_minor_updated_at 
    BEFORE UPDATE ON banking_asset_classes_minor 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_category_banking_mapping_updated_at 
    BEFORE UPDATE ON category_banking_mapping 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 11. Vérification des données insérées
SELECT 'Classes majeures créées:' as info;
SELECT name, description FROM banking_asset_classes_major ORDER BY name;

SELECT 'Sous-classes créées:' as info;
SELECT 
    mac.name as major_class,
    macm.name as minor_class,
    macm.description
FROM banking_asset_classes_major mac
JOIN banking_asset_classes_minor macm ON mac.id = macm.major_class_id
ORDER BY mac.name, macm.name;

SELECT 'Mapping des catégories:' as info;
SELECT 
    cbm.original_category,
    mac.name as major_class,
    macm.name as minor_class
FROM category_banking_mapping cbm
JOIN banking_asset_classes_major mac ON cbm.major_class_id = mac.id
JOIN banking_asset_classes_minor macm ON cbm.minor_class_id = macm.id
ORDER BY mac.name, macm.name; 