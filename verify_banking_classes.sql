-- Script de vérification des classes d'actifs bancaires
-- Exécuter après avoir lancé le script principal

-- 1. Vérifier les classes majeures
SELECT '=== CLASSES MAJEURES ===' as section;
SELECT 
    id,
    name,
    description,
    created_at
FROM banking_asset_classes_major 
ORDER BY name;

-- 2. Vérifier les sous-classes
SELECT '=== SOUS-CLASSES ===' as section;
SELECT 
    macm.id,
    mac.name as major_class,
    macm.name as minor_class,
    macm.description,
    macm.created_at
FROM banking_asset_classes_minor macm
JOIN banking_asset_classes_major mac ON macm.major_class_id = mac.id
ORDER BY mac.name, macm.name;

-- 3. Vérifier le mapping des catégories
SELECT '=== MAPPING DES CATÉGORIES ===' as section;
SELECT 
    cbm.original_category,
    mac.name as major_class,
    macm.name as minor_class,
    mac.description as major_description,
    macm.description as minor_description
FROM category_banking_mapping cbm
JOIN banking_asset_classes_major mac ON cbm.major_class_id = mac.id
JOIN banking_asset_classes_minor macm ON cbm.minor_class_id = macm.id
ORDER BY mac.name, macm.name;

-- 4. Tester la fonction de classification
SELECT '=== TEST FONCTION CLASSIFICATION ===' as section;
SELECT * FROM get_banking_classification('Actions');
SELECT * FROM get_banking_classification('Voitures');
SELECT * FROM get_banking_classification('Art');

-- 5. Vérifier la vue de résumé
SELECT '=== RÉSUMÉ PAR CLASSE D''ACTIF ===' as section;
SELECT 
    major_class,
    minor_class,
    item_count,
    ROUND(total_acquisition_value::numeric, 2) as total_acquisition_value,
    ROUND(total_current_value::numeric, 2) as total_current_value,
    ROUND(avg_acquisition_price::numeric, 2) as avg_acquisition_price
FROM banking_asset_class_summary
ORDER BY major_class, minor_class;

-- 6. Vérifier les items existants avec leur classification
SELECT '=== ITEMS AVEC CLASSIFICATION BANCAIRE ===' as section;
SELECT 
    i.name,
    i.category,
    mac.name as major_class,
    macm.name as minor_class,
    COALESCE(i.current_price * i.stock_quantity, i.acquisition_price, 0) as current_value
FROM items i
LEFT JOIN category_banking_mapping cbm ON i.category = cbm.original_category
LEFT JOIN banking_asset_classes_major mac ON cbm.major_class_id = mac.id
LEFT JOIN banking_asset_classes_minor macm ON cbm.minor_class_id = macm.id
WHERE i.status != 'Sold' OR i.status IS NULL
ORDER BY mac.name, macm.name, i.name;

-- 7. Statistiques par classe majeure
SELECT '=== STATISTIQUES PAR CLASSE MAJEURE ===' as section;
SELECT 
    mac.name as major_class,
    COUNT(DISTINCT i.id) as total_items,
    ROUND(SUM(COALESCE(i.current_price * i.stock_quantity, i.acquisition_price, 0))::numeric, 2) as total_value,
    ROUND(AVG(COALESCE(i.current_price * i.stock_quantity, i.acquisition_price, 0))::numeric, 2) as avg_value
FROM banking_asset_classes_major mac
LEFT JOIN category_banking_mapping cbm ON mac.id = cbm.major_class_id
LEFT JOIN items i ON cbm.original_category = i.category
WHERE (i.status != 'Sold' OR i.status IS NULL)
GROUP BY mac.id, mac.name
ORDER BY total_value DESC;

-- 8. Vérifier les contraintes et index
SELECT '=== VÉRIFICATION DES INDEX ===' as section;
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('banking_asset_classes_major', 'banking_asset_classes_minor', 'category_banking_mapping')
ORDER BY tablename, indexname;

-- 9. Vérifier les triggers
SELECT '=== VÉRIFICATION DES TRIGGERS ===' as section;
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE event_object_table IN ('banking_asset_classes_major', 'banking_asset_classes_minor', 'category_banking_mapping')
ORDER BY event_object_table, trigger_name; 