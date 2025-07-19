-- Script pour copier les données d'asking_price vers current_value
-- À exécuter si la colonne asking_price existe encore avec des données

-- 1. Vérifier si la colonne asking_price existe et contient des données
SELECT 
    CASE 
        WHEN EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'collection_items' AND column_name = 'asking_price')
        THEN '✅ Colonne asking_price existe'
        ELSE '❌ Colonne asking_price n''existe pas'
    END as asking_price_status;

-- 2. Compter les enregistrements avec asking_price non nul
SELECT 
    COUNT(*) as total_items,
    COUNT(asking_price) as items_with_asking_price,
    COUNT(current_value) as items_with_current_value,
    SUM(asking_price) as total_asking_price,
    SUM(current_value) as total_current_value
FROM collection_items;

-- 3. Copier les données d'asking_price vers current_value
UPDATE collection_items 
SET current_value = asking_price 
WHERE asking_price IS NOT NULL AND (current_value IS NULL OR current_value = 0);

-- 4. Vérifier le résultat de la copie
SELECT 
    COUNT(*) as total_items,
    COUNT(current_value) as items_with_current_value,
    SUM(current_value) as total_current_value
FROM collection_items 
WHERE current_value IS NOT NULL;

-- 5. Afficher quelques exemples de données copiées
SELECT 
    id,
    name,
    asking_price,
    current_value,
    CASE 
        WHEN asking_price = current_value THEN '✅ Copié'
        WHEN asking_price IS NULL AND current_value IS NOT NULL THEN '✅ Déjà présent'
        WHEN asking_price IS NOT NULL AND current_value IS NULL THEN '❌ Non copié'
        ELSE '⚠️ Différent'
    END as status
FROM collection_items 
WHERE asking_price IS NOT NULL OR current_value IS NOT NULL
ORDER BY id
LIMIT 10;

-- 6. Message de confirmation
SELECT '✅ Données copiées d''asking_price vers current_value avec succès !' as status; 