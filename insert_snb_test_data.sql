-- =====================================================
-- DONNÉES DE TEST SNB (SEPTEMBRE 2025)
-- Basées sur les communiqués officiels BNS
-- À exécuter dans Supabase SQL Editor
-- =====================================================

-- 1. CPI (Inflation août 2025) - Source: Communiqué BNS 25.09.2025
-- "L'inflation est passée de -0,1% en mai à 0,2% en août"
INSERT INTO snb_cpi_data (provider, as_of, yoy_pct, mm_pct, source_url, idempotency_key)
VALUES ('BFS', '2025-08-31', 0.2, NULL, 'https://www.bfs.admin.ch', 'bfs-2025-08-real')
ON CONFLICT (idempotency_key) DO NOTHING;

-- 2. KOF Barometer (septembre 2025)
-- Valeur approximative basée sur "croissance modeste" mentionnée
INSERT INTO snb_kof_data (provider, as_of, barometer, source_url, idempotency_key)
VALUES ('KOF', '2025-09-30', 97.5, 'https://kof.ethz.ch', 'kof-2025-09-real')
ON CONFLICT (idempotency_key) DO NOTHING;

-- 3. Prévisions BNS (MPA 25 septembre 2025)
-- "0,2% pour 2025, 0,5% pour 2026 et 0,7% pour 2027"
INSERT INTO snb_forecasts (meeting_date, forecast, source_url, pdf_url, idempotency_key)
VALUES (
    '2025-09-25',
    '{"2025": 0.2, "2026": 0.5, "2027": 0.7}'::jsonb,
    'https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/monetary-policy-assessment',
    'https://www.snb.ch/en/publications/communication/monetary-policy-assessments/2025-09-25.pdf',
    'snb-mpa-2025-09-25-official'
)
ON CONFLICT (idempotency_key) DO NOTHING;

-- 4. Courbe OIS (approximative basée sur taux 0%)
-- Sera remplacée par données Eurex réelles via scraping
INSERT INTO snb_ois_data (as_of, points, source_url, idempotency_key)
VALUES (
    '2025-09-30',
    '[
        {"tenor_months": 3, "rate_pct": 0.00},
        {"tenor_months": 6, "rate_pct": 0.05},
        {"tenor_months": 9, "rate_pct": 0.08},
        {"tenor_months": 12, "rate_pct": 0.10},
        {"tenor_months": 18, "rate_pct": 0.15},
        {"tenor_months": 24, "rate_pct": 0.20}
    ]'::jsonb,
    'https://www.eurex.com (approximation, sera mise à jour par scraping)',
    'ois-2025-09-30-initial'
)
ON CONFLICT (idempotency_key) DO NOTHING;

-- 5. Vérifier/Mettre à jour le taux directeur actuel
UPDATE snb_config 
SET value = '0.0'::jsonb, updated_at = NOW()
WHERE key = 'policy_rate_now_pct';

-- Vérification
SELECT 
    'CPI' as source, COUNT(*) as count FROM snb_cpi_data
UNION ALL
SELECT 'KOF', COUNT(*) FROM snb_kof_data
UNION ALL
SELECT 'SNB Forecasts', COUNT(*) FROM snb_forecasts
UNION ALL
SELECT 'OIS', COUNT(*) FROM snb_ois_data
UNION ALL
SELECT 'Config', COUNT(*) FROM snb_config;

-- Afficher les dernières valeurs
SELECT 'CPI YoY' as metric, yoy_pct::text as value, as_of::text as date FROM snb_cpi_data ORDER BY as_of DESC LIMIT 1
UNION ALL
SELECT 'KOF', barometer::text, as_of::text FROM snb_kof_data ORDER BY as_of DESC LIMIT 1
UNION ALL
SELECT 'Policy Rate', value::text, updated_at::date::text FROM snb_config WHERE key = 'policy_rate_now_pct';

