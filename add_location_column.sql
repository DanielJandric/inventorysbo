-- Script pour ajouter la colonne location à la table items
-- Ajout de la colonne location avec les valeurs prédéfinies

-- Vérifier si la colonne existe déjà
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'items' 
        AND column_name = 'location'
    ) THEN
        -- Ajouter la colonne location
        ALTER TABLE items ADD COLUMN location VARCHAR(50);
        
        -- Ajouter un commentaire pour documenter les valeurs possibles
        COMMENT ON COLUMN items.location IS 'Localisation de l''objet: St-Sulpice, Genève, Schindellegi, Crans, Sion, Anzère, St-Tropez, Marbella, London, Zurich, Autre';
        
        RAISE NOTICE 'Colonne location ajoutée avec succès';
    ELSE
        RAISE NOTICE 'La colonne location existe déjà';
    END IF;
END $$;

-- Vérifier le résultat
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'items' 
AND column_name = 'location'; 