# 🗄️ Guide de Configuration de la Base de Données

## 📋 Vue d'ensemble

Ce guide vous aide à configurer la base de données Supabase pour stocker les analyses de marché générées par le Background Worker.

## 🔧 Prérequis

- Accès à votre dashboard Supabase
- Variables d'environnement configurées (`SUPABASE_URL` et `SUPABASE_KEY`)

## 📊 Structure de la Base de Données

### Table `market_analyses`

La table stocke toutes les analyses de marché générées par le Background Worker :

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL | Clé primaire auto-incrémentée |
| `timestamp` | TIMESTAMP | Horodatage de l'analyse |
| `analysis_type` | VARCHAR(100) | Type d'analyse ('automatic', 'manual', 'test') |
| `summary` | TEXT | Résumé de l'analyse |
| `key_points` | JSONB | Points clés de l'analyse |
| `structured_data` | JSONB | Données structurées (prix, tendances, volumes) |
| `insights` | JSONB | Insights et observations |
| `risks` | JSONB | Risques identifiés |
| `opportunities` | JSONB | Opportunités identifiées |
| `sources` | JSONB | Sources utilisées |
| `confidence_score` | DECIMAL(3,2) | Score de confiance (0.00-1.00) |
| `worker_status` | VARCHAR(50) | Statut du worker ('completed', 'error', 'processing') |
| `processing_time_seconds` | INTEGER | Temps de traitement en secondes |
| `error_message` | TEXT | Message d'erreur si applicable |
| `created_at` | TIMESTAMP | Date de création |
| `updated_at` | TIMESTAMP | Date de mise à jour |

## 🚀 Configuration

### Étape 1: Accéder à Supabase

1. Allez sur [supabase.com](https://supabase.com)
2. Connectez-vous à votre compte
3. Sélectionnez votre projet

### Étape 2: Créer la Table

1. Dans votre dashboard Supabase, allez dans **SQL Editor**
2. Cliquez sur **New Query**
3. Copiez-collez le script SQL suivant :

```sql
-- Création de la table market_analyses pour le Background Worker
CREATE TABLE IF NOT EXISTS market_analyses (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_type VARCHAR(100) NOT NULL DEFAULT 'automatic',
    summary TEXT,
    key_points JSONB,
    structured_data JSONB,
    insights JSONB,
    risks JSONB,
    opportunities JSONB,
    sources JSONB,
    confidence_score DECIMAL(3,2),
    worker_status VARCHAR(50) DEFAULT 'completed',
    processing_time_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_market_analyses_timestamp ON market_analyses(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_analyses_type ON market_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_market_analyses_status ON market_analyses(worker_status);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour mettre à jour updated_at
CREATE TRIGGER update_market_analyses_updated_at 
    BEFORE UPDATE ON market_analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insertion d'un exemple de données pour test
INSERT INTO market_analyses (
    analysis_type,
    summary,
    key_points,
    structured_data,
    insights,
    risks,
    opportunities,
    sources,
    confidence_score,
    worker_status
) VALUES (
    'automatic',
    'Analyse automatique générée par le Background Worker. Les marchés montrent une tendance positive avec un focus particulier sur l''IA.',
    '["Marchés en hausse avec focus sur l''IA", "Tendances technologiques positives", "Investissements dans l''intelligence artificielle"]',
    '{"prix": "Tendance haussière", "tendance": "Positive", "volumes": "Élevés"}',
    '["L''IA continue d''attirer les investissements"]',
    '["Volatilité possible"]',
    '["Croissance technologique"]',
    '[{"title": "Background Worker Analysis", "url": "#"}]',
    0.85,
    'completed'
) ON CONFLICT DO NOTHING;
```

4. Cliquez sur **Run** pour exécuter le script

### Étape 3: Vérifier la Configuration

1. Allez dans **Table Editor**
2. Vérifiez que la table `market_analyses` a été créée
3. Vérifiez qu'une ligne de test a été insérée

## 🔄 Mise à Jour du Background Worker

### Variables d'Environnement Requises

Assurez-vous que votre Background Worker sur Render a ces variables :

```
SUPABASE_URL=votre_url_supabase
SUPABASE_KEY=votre_clé_supabase
SCRAPINGBEE_API_KEY=votre_clé_scrapingbee
OPENAI_API_KEY=votre_clé_openai
```

### Redéploiement

1. Allez sur votre dashboard Render
2. Sélectionnez votre Background Worker
3. Cliquez sur **Manual Deploy** > **Deploy latest commit**

## 🧪 Test de l'Intégration

### Test Local

```bash
python test_database_integration.py
```

### Test de l'Application Web

1. Démarrez votre application web
2. Allez dans l'onglet **Marchés**
3. Cliquez sur **Récupérer Analyse**
4. Vérifiez que les données s'affichent correctement

## 📊 Monitoring

### Vérifier les Analyses

```sql
-- Voir toutes les analyses
SELECT * FROM market_analyses ORDER BY timestamp DESC;

-- Voir les dernières analyses
SELECT id, timestamp, analysis_type, summary, confidence_score 
FROM market_analyses 
ORDER BY timestamp DESC 
LIMIT 10;

-- Voir les erreurs
SELECT * FROM market_analyses WHERE worker_status = 'error';
```

### Statistiques

```sql
-- Nombre d'analyses par type
SELECT analysis_type, COUNT(*) as count 
FROM market_analyses 
GROUP BY analysis_type;

-- Score de confiance moyen
SELECT AVG(confidence_score) as avg_confidence 
FROM market_analyses 
WHERE confidence_score IS NOT NULL;
```

## 🔧 Dépannage

### Problème: Connexion à Supabase échoue

**Solution:**
1. Vérifiez vos variables d'environnement
2. Testez la connexion : `python setup_database.py`

### Problème: Table non trouvée

**Solution:**
1. Vérifiez que le script SQL a été exécuté
2. Vérifiez les permissions dans Supabase

### Problème: Aucune analyse disponible

**Solution:**
1. Vérifiez que le Background Worker fonctionne
2. Vérifiez les logs du Background Worker
3. Testez manuellement : `python test_database_integration.py`

## 📈 Optimisations

### Index Recommandés

```sql
-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_market_analyses_recent 
ON market_analyses(timestamp DESC) 
WHERE worker_status = 'completed';

-- Index pour les analyses par type
CREATE INDEX IF NOT EXISTS idx_market_analyses_type_status 
ON market_analyses(analysis_type, worker_status);
```

### Nettoyage Automatique

```sql
-- Supprimer les anciennes analyses (optionnel)
DELETE FROM market_analyses 
WHERE timestamp < NOW() - INTERVAL '30 days';
```

## ✅ Checklist de Configuration

- [ ] Table `market_analyses` créée
- [ ] Index créés
- [ ] Trigger `update_updated_at_column` configuré
- [ ] Données de test insérées
- [ ] Variables d'environnement configurées
- [ ] Background Worker redéployé
- [ ] Test d'intégration réussi
- [ ] Application web fonctionnelle

## 🎯 Résultat Attendu

Après la configuration, vous devriez avoir :

1. **Base de données opérationnelle** avec stockage des analyses
2. **Background Worker fonctionnel** qui sauvegarde automatiquement
3. **Application web** qui récupère les analyses depuis la base de données
4. **Plus de timeouts** dans l'application web
5. **Analyses persistantes** disponibles même après redémarrage

## 📞 Support

Si vous rencontrez des problèmes :

1. Vérifiez les logs du Background Worker
2. Testez la connexion à Supabase
3. Vérifiez les variables d'environnement
4. Consultez les logs de l'application web 