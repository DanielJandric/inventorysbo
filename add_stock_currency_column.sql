-- Script pour ajouter les colonnes manquantes pour les actions boursières
-- Exécutez ce script dans votre base de données Supabase

-- Ajouter la colonne stock_currency si elle n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_currency'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_currency VARCHAR(10) DEFAULT 'CHF';
        RAISE NOTICE 'Colonne stock_currency ajoutée';
    ELSE
        RAISE NOTICE 'Colonne stock_currency existe déjà';
    END IF;
END $$;

-- Ajouter les autres colonnes de métriques boursières si elles n'existent pas
DO $$ 
BEGIN
    -- stock_volume
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_volume'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_volume BIGINT;
        RAISE NOTICE 'Colonne stock_volume ajoutée';
    END IF;
    
    -- stock_pe_ratio
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_pe_ratio'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_pe_ratio DECIMAL(10,2);
        RAISE NOTICE 'Colonne stock_pe_ratio ajoutée';
    END IF;
    
    -- stock_52_week_high
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_52_week_high'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_52_week_high DECIMAL(10,2);
        RAISE NOTICE 'Colonne stock_52_week_high ajoutée';
    END IF;
    
    -- stock_52_week_low
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_52_week_low'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_52_week_low DECIMAL(10,2);
        RAISE NOTICE 'Colonne stock_52_week_low ajoutée';
    END IF;
    
    -- stock_change
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_change'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_change DECIMAL(10,2);
        RAISE NOTICE 'Colonne stock_change ajoutée';
    END IF;
    
    -- stock_change_percent
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_change_percent'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_change_percent DECIMAL(10,2);
        RAISE NOTICE 'Colonne stock_change_percent ajoutée';
    END IF;
    
    -- stock_average_volume
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' AND column_name = 'stock_average_volume'
    ) THEN
        ALTER TABLE items ADD COLUMN stock_average_volume BIGINT;
        RAISE NOTICE 'Colonne stock_average_volume ajoutée';
    END IF;
END $$;

-- Mettre à jour les actions existantes pour avoir CHF par défaut
UPDATE items 
SET stock_currency = 'CHF' 
WHERE category = 'Actions' AND (stock_currency IS NULL OR stock_currency = '');

-- Vérifier que toutes les colonnes ont été ajoutées
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    CASE 
        WHEN column_name IN ('stock_currency', 'stock_volume', 'stock_pe_ratio', 'stock_52_week_high', 'stock_52_week_low', 'stock_change', 'stock_change_percent', 'stock_average_volume') 
        THEN '✅ Ajoutée' 
        ELSE '❌ Manquante' 
    END as status
FROM information_schema.columns 
WHERE table_name = 'items' 
AND column_name IN ('stock_currency', 'stock_volume', 'stock_pe_ratio', 'stock_52_week_high', 'stock_52_week_low', 'stock_change', 'stock_change_percent', 'stock_average_volume')
ORDER BY column_name; 