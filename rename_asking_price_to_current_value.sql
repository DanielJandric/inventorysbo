-- Script pour renommer "prix demandé" en "valeur actuelle"
-- Date: $(date)
-- Description: Renomme la colonne asking_price en current_value et met à jour les commentaires

-- 1. Vérifier si la table existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'collection_items') THEN
        RAISE EXCEPTION 'La table collection_items n''existe pas. Veuillez d''abord exécuter create_database_schema.sql';
    END IF;
END $$;

-- 2. Vérifier si la colonne asking_price existe
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'collection_items' AND column_name = 'asking_price') THEN
        -- Renommer la colonne asking_price en current_value
        ALTER TABLE collection_items RENAME COLUMN asking_price TO current_value;
        RAISE NOTICE 'Colonne asking_price renommée en current_value';
    ELSE
        RAISE NOTICE 'La colonne asking_price n''existe pas. La colonne current_value existe déjà.';
    END IF;
END $$;

-- 3. Mettre à jour le commentaire de la colonne
COMMENT ON COLUMN collection_items.current_value IS 'Valeur actuelle de l''objet en CHF';

-- 4. Mettre à jour la contrainte de vérification des prix
ALTER TABLE collection_items DROP CONSTRAINT IF EXISTS chk_prices;
ALTER TABLE collection_items ADD CONSTRAINT chk_prices CHECK (current_value >= 0 AND sold_price >= 0 AND acquisition_price >= 0 AND current_price >= 0);

-- 5. Vérifier que la modification s'est bien passée
SELECT column_name, data_type, is_nullable, column_default, col_description((table_schema||'.'||table_name)::regclass, ordinal_position) as comment
FROM information_schema.columns 
WHERE table_name = 'collection_items' AND column_name = 'current_value';

-- 6. Afficher un résumé des données
SELECT 
    COUNT(*) as total_items,
    COUNT(current_value) as items_with_current_value,
    AVG(current_value) as average_current_value,
    SUM(current_value) as total_current_value
FROM collection_items 
WHERE status = 'Available' AND current_value IS NOT NULL;

-- 7. Message de confirmation
SELECT '✅ Migration asking_price → current_value terminée avec succès !' as status; 