-- Ajouter la colonne executive_summary à la table market_analyses
ALTER TABLE market_analyses 
ADD COLUMN IF NOT EXISTS executive_summary JSONB;

-- Commentaire sur la colonne
COMMENT ON COLUMN market_analyses.executive_summary IS 'Executive summary avec 5 bullet points percutants de l''analyse';
