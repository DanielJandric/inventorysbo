-- Script SQL pour corriger les problèmes IREN et devises
-- À exécuter dans l'éditeur SQL de Supabase

-- 1. Vérifier l'état actuel des items IREN
SELECT 
    id,
    name,
    stock_symbol,
    stock_exchange,
    stock_currency,
    current_price,
    last_price_update
FROM items 
WHERE stock_symbol ILIKE '%IREN%'
ORDER BY id;

-- 2. Corriger le symbole IREN pour utiliser l'action suisse
UPDATE items 
SET 
    stock_symbol = 'IREN.SW',
    stock_exchange = 'SWX',
    stock_currency = 'CHF'
WHERE stock_symbol ILIKE '%IREN%' 
AND stock_symbol != 'IREN.SW';

-- 3. Corriger les devises des actions selon leur exchange
-- Actions suisses (.SW)
UPDATE items 
SET stock_currency = 'CHF'
WHERE category = 'Actions' 
AND (stock_symbol LIKE '%.SW' OR stock_exchange IN ('SWX', 'SW'))
AND stock_currency != 'CHF';

-- Actions américaines (sans suffixe ou avec .US)
UPDATE items 
SET stock_currency = 'USD'
WHERE category = 'Actions' 
AND stock_symbol NOT LIKE '%.SW' 
AND stock_symbol NOT LIKE '%.L' 
AND stock_symbol NOT LIKE '%.PA' 
AND stock_symbol NOT LIKE '%.MI' 
AND stock_symbol NOT LIKE '%.AS' 
AND stock_symbol NOT LIKE '%.VI' 
AND stock_symbol NOT LIKE '%.ST' 
AND stock_symbol NOT LIKE '%.OL' 
AND stock_symbol NOT LIKE '%.CO' 
AND stock_symbol NOT LIKE '%.HE' 
AND stock_symbol NOT LIKE '%.IC' 
AND stock_exchange NOT IN ('SWX', 'SW', 'LSE', 'FRA', 'EPA', 'MIL', 'AMS', 'VIE', 'STO', 'OSL', 'CPH', 'HEL', 'ICE')
AND stock_currency != 'USD';

-- Actions européennes
UPDATE items 
SET stock_currency = 'EUR'
WHERE category = 'Actions' 
AND (stock_symbol LIKE '%.L' OR stock_symbol LIKE '%.PA' OR stock_symbol LIKE '%.MI' OR stock_symbol LIKE '%.AS' OR stock_symbol LIKE '%.VI')
AND stock_exchange IN ('LSE', 'FRA', 'EPA', 'MIL', 'AMS', 'VIE')
AND stock_currency != 'EUR';

-- Actions britanniques
UPDATE items 
SET stock_currency = 'GBP'
WHERE category = 'Actions' 
AND stock_symbol LIKE '%.L'
AND stock_exchange = 'LSE'
AND stock_currency != 'GBP';

-- 4. Ajouter la colonne stock_currency si elle n'existe pas
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

-- 5. Vérifier le résultat
SELECT 
    'Actions corrigées' as status,
    COUNT(*) as total_actions,
    COUNT(CASE WHEN stock_currency = 'CHF' THEN 1 END) as chf_actions,
    COUNT(CASE WHEN stock_currency = 'USD' THEN 1 END) as usd_actions,
    COUNT(CASE WHEN stock_currency = 'EUR' THEN 1 END) as eur_actions,
    COUNT(CASE WHEN stock_currency = 'GBP' THEN 1 END) as gbp_actions
FROM items 
WHERE category = 'Actions';

-- 6. Afficher les actions avec leurs devises
SELECT 
    id,
    name,
    stock_symbol,
    stock_exchange,
    stock_currency,
    current_price,
    last_price_update
FROM items 
WHERE category = 'Actions'
ORDER BY stock_currency, stock_symbol;

-- 7. Vérifier spécifiquement IREN
SELECT 
    id,
    name,
    stock_symbol,
    stock_exchange,
    stock_currency,
    current_price,
    last_price_update
FROM items 
WHERE stock_symbol ILIKE '%IREN%'
ORDER BY id; 