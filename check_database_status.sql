-- Script pour vérifier l'état actuel de la base de données
-- À exécuter avant de faire des modifications

-- 1. Vérifier si la table collection_items existe
SELECT 
    CASE 
        WHEN EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'collection_items') 
        THEN '✅ Table collection_items existe'
        ELSE '❌ Table collection_items n''existe pas'
    END as table_status;

-- 2. Si la table existe, afficher sa structure
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'collection_items') THEN
        RAISE NOTICE 'Structure de la table collection_items:';
    END IF;
END $$;

SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default,
    CASE 
        WHEN column_name = 'asking_price' THEN '❌ Ancien nom - à renommer'
        WHEN column_name = 'current_value' THEN '✅ Nouveau nom - correct'
        ELSE '✅ Autre colonne'
    END as status
FROM information_schema.columns 
WHERE table_name = 'collection_items' 
ORDER BY ordinal_position;

-- 3. Vérifier les contraintes
SELECT 
    constraint_name,
    constraint_type,
    table_name
FROM information_schema.table_constraints 
WHERE table_name = 'collection_items';

-- 4. Compter les enregistrements
SELECT 
    COUNT(*) as total_items,
    COUNT(CASE WHEN status = 'Available' THEN 1 END) as available_items,
    COUNT(CASE WHEN status = 'Sold' THEN 1 END) as sold_items,
    COUNT(CASE WHEN status = 'Reserved' THEN 1 END) as reserved_items
FROM collection_items;

-- 5. Vérifier les colonnes de prix/valeur
SELECT 
    'asking_price' as column_name,
    COUNT(*) as items_with_value,
    AVG(asking_price) as average_value,
    SUM(asking_price) as total_value
FROM collection_items 
WHERE asking_price IS NOT NULL
UNION ALL
SELECT 
    'current_value' as column_name,
    COUNT(*) as items_with_value,
    AVG(current_value) as average_value,
    SUM(current_value) as total_value
FROM collection_items 
WHERE current_value IS NOT NULL;

-- 6. Recommandations
SELECT 
    CASE 
        WHEN EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'collection_items' AND column_name = 'asking_price')
        THEN '🔧 Action requise: Exécuter rename_asking_price_to_current_value.sql'
        WHEN EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'collection_items' AND column_name = 'current_value')
        THEN '✅ Base de données à jour - colonne current_value existe'
        ELSE '❌ Problème: Aucune colonne de valeur trouvée'
    END as recommendation; 