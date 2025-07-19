-- Script de rollback pour supprimer les classes d'actifs bancaires
-- ATTENTION: Ce script supprime définitivement toutes les données bancaires
-- Exécuter seulement si vous voulez tout supprimer

-- 1. Supprimer les triggers
DROP TRIGGER IF EXISTS update_banking_asset_classes_major_updated_at ON banking_asset_classes_major;
DROP TRIGGER IF EXISTS update_banking_asset_classes_minor_updated_at ON banking_asset_classes_minor;
DROP TRIGGER IF EXISTS update_category_banking_mapping_updated_at ON category_banking_mapping;

-- 2. Supprimer la fonction de mise à jour
DROP FUNCTION IF EXISTS update_updated_at_column();

-- 3. Supprimer la fonction de classification
DROP FUNCTION IF EXISTS get_banking_classification(VARCHAR);

-- 4. Supprimer la vue de résumé
DROP VIEW IF EXISTS banking_asset_class_summary;

-- 5. Supprimer les index
DROP INDEX IF EXISTS idx_category_banking_mapping_original;
DROP INDEX IF EXISTS idx_banking_asset_classes_major_name;
DROP INDEX IF EXISTS idx_banking_asset_classes_minor_major_id;

-- 6. Supprimer les tables dans l'ordre (à cause des contraintes de clés étrangères)
DROP TABLE IF EXISTS category_banking_mapping;
DROP TABLE IF EXISTS banking_asset_classes_minor;
DROP TABLE IF EXISTS banking_asset_classes_major;

-- 7. Vérification que tout a été supprimé
SELECT '=== VÉRIFICATION SUPPRESSION ===' as info;

SELECT 'Tables restantes:' as check_type;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%banking%'
ORDER BY table_name;

SELECT 'Fonctions restantes:' as check_type;
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name LIKE '%banking%'
ORDER BY routine_name;

SELECT 'Vues restantes:' as check_type;
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE '%banking%'
ORDER BY table_name;

SELECT 'Rollback terminé avec succès!' as status; 