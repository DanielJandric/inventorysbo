# Guide de Configuration Supabase - Update Marchés

## Création Manuelle de la Table

Si le script automatique ne fonctionne pas, suivez ces étapes pour créer la table manuellement :

### 1. Accéder à Supabase
1. Connectez-vous à votre projet Supabase
2. Allez dans l'onglet "SQL Editor"
3. Cliquez sur "New query"

### 2. Exécuter le SQL
Copiez et collez ce code SQL :

```sql
-- Création de la table market_updates pour les briefings de marché
CREATE TABLE IF NOT EXISTS market_updates (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    date VARCHAR(10) NOT NULL,
    time VARCHAR(5) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trigger_type VARCHAR(20) DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'scheduled')),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_market_updates_created_at ON market_updates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_updates_date ON market_updates(date DESC);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_market_updates_updated_at 
    BEFORE UPDATE ON market_updates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Commentaires pour la documentation
COMMENT ON TABLE market_updates IS 'Table pour stocker les briefings de marché générés automatiquement ou manuellement';
COMMENT ON COLUMN market_updates.content IS 'Contenu du briefing de marché généré par GPT-4o';
COMMENT ON COLUMN market_updates.date IS 'Date du briefing au format YYYY-MM-DD';
COMMENT ON COLUMN market_updates.time IS 'Heure de génération au format HH:MM';
COMMENT ON COLUMN market_updates.trigger_type IS 'Type de déclenchement: manual ou scheduled';
```

### 3. Exécuter
1. Cliquez sur "Run" pour exécuter le SQL
2. Vérifiez que la table a été créée dans l'onglet "Table Editor"

### 4. Vérification
Dans l'onglet "Table Editor", vous devriez voir :
- ✅ Table `market_updates` créée
- ✅ Colonnes : id, content, date, time, created_at, trigger_type, updated_at
- ✅ Index créés automatiquement

## Configuration RLS (Row Level Security)

Si vous utilisez RLS, ajoutez cette politique :

```sql
-- Activer RLS sur la table
ALTER TABLE market_updates ENABLE ROW LEVEL SECURITY;

-- Politique pour permettre l'insertion et la lecture
CREATE POLICY "Enable all operations for authenticated users" ON market_updates
    FOR ALL USING (auth.role() = 'authenticated');
```

## Test de la Fonctionnalité

Une fois la table créée :

1. **Déployez l'application** sur Render
2. **Accédez à** `/markets` dans votre application
3. **Testez le bouton** "Générer Update"
4. **Vérifiez** que le briefing apparaît dans la liste

## Dépannage

### Erreur "relation does not exist"
- Vérifiez que le SQL a été exécuté avec succès
- Vérifiez que vous êtes dans le bon projet Supabase

### Erreur de permissions
- Vérifiez que votre clé API Supabase a les bonnes permissions
- Vérifiez les politiques RLS si activées

### Erreur de connexion
- Vérifiez les variables d'environnement `SUPABASE_URL` et `SUPABASE_KEY`
- Vérifiez que l'application peut accéder à Supabase 