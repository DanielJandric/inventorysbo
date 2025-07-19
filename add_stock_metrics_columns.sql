-- Script pour ajouter les colonnes de métriques boursières à la table collection_items
-- À exécuter dans l'éditeur SQL de Supabase

-- Ajouter les nouvelles colonnes pour les métriques boursières
ALTER TABLE collection_items 
ADD COLUMN IF NOT EXISTS stock_volume BIGINT,
ADD COLUMN IF NOT EXISTS stock_pe_ratio DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_52_week_high DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_52_week_low DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_change DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_change_percent DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS stock_average_volume BIGINT;

-- Ajouter des commentaires pour documenter les colonnes
COMMENT ON COLUMN collection_items.stock_volume IS 'Volume de transactions de l''action';
COMMENT ON COLUMN collection_items.stock_pe_ratio IS 'Ratio P/E (Price/Earnings) de l''action';
COMMENT ON COLUMN collection_items.stock_52_week_high IS 'Plus haut sur 52 semaines';
COMMENT ON COLUMN collection_items.stock_52_week_low IS 'Plus bas sur 52 semaines';
COMMENT ON COLUMN collection_items.stock_change IS 'Variation du prix (absolue)';
COMMENT ON COLUMN collection_items.stock_change_percent IS 'Variation du prix (pourcentage)';
COMMENT ON COLUMN collection_items.stock_average_volume IS 'Volume moyen sur 30 jours';

-- Vérifier que les colonnes ont été ajoutées
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'collection_items' 
AND column_name LIKE 'stock_%'
ORDER BY column_name; 