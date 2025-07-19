-- Script final pour ajouter les colonnes de métriques boursières à la table items
-- À exécuter dans l'éditeur SQL de Supabase

-- 1. Vérifier les colonnes existantes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'items' 
ORDER BY ordinal_position;

-- 2. Ajouter les colonnes manquantes
ALTER TABLE items 
ADD COLUMN IF NOT EXISTS stock_symbol VARCHAR(20),
ADD COLUMN IF NOT EXISTS stock_quantity INTEGER,
ADD COLUMN IF NOT EXISTS stock_purchase_price DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS stock_exchange VARCHAR(50),
ADD COLUMN IF NOT EXISTS current_price DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS last_price_update TIMESTAMP,
ADD COLUMN IF NOT EXISTS stock_volume BIGINT,
ADD COLUMN IF NOT EXISTS stock_pe_ratio DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_52_week_high DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_52_week_low DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_change DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS stock_change_percent DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS stock_average_volume BIGINT,
ADD COLUMN IF NOT EXISTS sale_status VARCHAR(50) DEFAULT 'initial',
ADD COLUMN IF NOT EXISTS sale_progress TEXT,
ADD COLUMN IF NOT EXISTS buyer_contact TEXT,
ADD COLUMN IF NOT EXISTS intermediary TEXT,
ADD COLUMN IF NOT EXISTS current_offer DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS last_action_date DATE,
ADD COLUMN IF NOT EXISTS surface_m2 DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS rental_income_chf DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- 3. Vérifier le résultat
SELECT 
    'Colonnes ajoutées avec succès' as status,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'items';

-- 4. Afficher les colonnes liées aux actions
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'items' 
AND (column_name LIKE 'stock_%' OR column_name = 'current_price' OR column_name = 'last_price_update')
ORDER BY column_name; 