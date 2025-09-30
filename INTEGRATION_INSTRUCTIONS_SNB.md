# 📋 INSTRUCTIONS D'INTÉGRATION SNB TAUX

## ✅ Étapes à suivre dans l'ordre

### ÉTAPE 1: Exécuter le script SQL dans Supabase

1. Ouvrez Supabase Dashboard → SQL Editor
2. Copiez le contenu de `create_snb_tables.sql`
3. Exécutez le script
4. Vérifiez que les 5 tables sont créées :
   - `snb_cpi_data`
   - `snb_kof_data`
   - `snb_forecasts`
   - `snb_ois_data`
   - `snb_model_runs`
   - `snb_config`

---

### ÉTAPE 2: Modifier app.py

#### A) Ajouter l'import du blueprint SNB

**Position:** Ligne ~76 (après les autres imports, avant le `# Load environment variables`)

```python
from snb_routes import snb_bp
```

#### B) Passer le client Supabase à l'app config

**Position:** Ligne ~2360 (juste après `CORS(app)`)

**Cherchez:**
```python
CORS(app)
# Register metrics blueprint under /api
```

**Ajoutez AVANT le `# Register metrics blueprint` :**
```python
CORS(app)

# Configure Supabase client in app context (pour snb_routes)
if supabase:
    app.config['SUPABASE_CLIENT'] = supabase

# Register metrics blueprint under /api
```

#### C) Enregistrer le blueprint SNB

**Position:** Ligne ~2366 (après `app.register_blueprint(metrics_bp, ...)`)

**Ajoutez:**
```python
# Register SNB Policy Engine blueprint
try:
    app.register_blueprint(snb_bp)
    logger.info("✅ SNB Policy Engine blueprint registered")
except Exception as e:
    logger.error(f"❌ Failed to register SNB blueprint: {e}")
```

#### D) Ajouter la route pour la page SNB Taux

**Position:** Ligne ~4200 (après la route `/sold`, avant `/real-estate`)

**Ajoutez:**
```python
@app.route("/snb-taux")
def snb_taux_page():
    """Page Prévision SNB Taux"""
    try:
        return render_template('snb_taux.html')
    except Exception as e:
        logger.error(f"Erreur rendu SNB Taux: {e}")
        return make_response(f"Erreur de rendu: {e}", 500)
```

---

### ÉTAPE 3: Ajouter le lien dans le menu hamburger (index.html)

**Fichier:** `templates/index.html`
**Position:** Ligne ~956 (après le lien "Update Marchés", avant "Settings")

**Cherchez:**
```html
                    <a href="/markets" class="menu-item">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                        <span>Update Marchés</span>
                    </a>
```

**Ajoutez APRÈS:**
```html
                    <a href="/snb-taux" class="menu-item">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        <span>SNB Taux</span>
                    </a>
```

---

### ÉTAPE 4: Tester l'installation

#### A) Redémarrer l'application
```bash
# Si développement local
python app.py

# Si Render/production, redéployez
```

#### B) Vérifier les logs
Vous devriez voir :
```
✅ SNB Policy Engine blueprint registered
```

#### C) Tester l'accès à la page
```
http://localhost:5000/snb-taux
```

Vous devriez voir :
- ✅ La page se charge (même si vide car pas de données)
- ⚠️ Message: "Erreur de chargement du modèle. Vérifiez que des données ont été ingérées."

---

### ÉTAPE 5: Insérer des données de test

#### A) Insérer des données CPI (Supabase SQL Editor)
```sql
INSERT INTO snb_cpi_data (provider, as_of, yoy_pct, mm_pct, source_url, idempotency_key)
VALUES ('BFS', '2025-09-30', 0.2, -0.1, 'https://www.bfs.admin.ch', 'bfs-2025-09-test');
```

#### B) Insérer des données KOF
```sql
INSERT INTO snb_kof_data (provider, as_of, barometer, source_url, idempotency_key)
VALUES ('KOF', '2025-09-01', 97.4, 'https://kof.ethz.ch', 'kof-2025-09-test');
```

#### C) Insérer des prévisions SNB
```sql
INSERT INTO snb_forecasts (meeting_date, forecast, source_url, pdf_url, idempotency_key)
VALUES ('2025-09-25', '{"2025": 0.2, "2026": 0.5, "2027": 0.7}', 'https://www.snb.ch', 'https://www.snb.ch/mpa.pdf', 'snb-mpa-2025-09-test');
```

#### D) Insérer des données OIS
```sql
INSERT INTO snb_ois_data (as_of, points, source_url, idempotency_key)
VALUES (
    '2025-09-30',
    '[
        {"tenor_months": 3, "rate_pct": 0.00},
        {"tenor_months": 6, "rate_pct": 0.01},
        {"tenor_months": 9, "rate_pct": 0.05},
        {"tenor_months": 12, "rate_pct": 0.10},
        {"tenor_months": 18, "rate_pct": 0.15},
        {"tenor_months": 24, "rate_pct": 0.20}
    ]',
    'https://www.eurex.com',
    'ois-2025-09-30-test'
);
```

---

### ÉTAPE 6: Tester le calcul du modèle

#### A) Via l'interface web
1. Allez sur `http://localhost:5000/snb-taux`
2. La page devrait maintenant afficher les KPIs
3. Cliquez sur "Recalculer" dans la section Scénario

#### B) Via API (cURL/Postman)
```bash
# Lancer le calcul
curl -X POST http://localhost:5000/api/snb/model/run \
  -H "Content-Type: application/json" \
  -d '{}'

# Récupérer le dernier résultat
curl http://localhost:5000/api/snb/model/latest
```

---

### ÉTAPE 7: Tester l'explication GPT-5

#### Pré-requis
- Votre clé OpenAI API doit être configurée dans `.env` ou `config.py`
- Variable: `OPENAI_API_KEY`

#### Test
```bash
curl -X POST http://localhost:5000/api/snb/explain \
  -H "Content-Type: application/json" \
  -d '{
    "model": {
      "as_of": "2025-09-30",
      "inputs": {"policy_rate_now_pct": 0.0, "cpi_yoy_pct": 0.2, "kof_barometer": 97.4},
      "probs": {"cut": 0.076, "hold": 0.848, "hike": 0.076}
    }
  }'
```

---

## 🔧 Dépannage

### Erreur: "Supabase not available"
- Vérifiez que `SUPABASE_URL` et `SUPABASE_KEY` sont configurés
- Vérifiez que le client Supabase est bien initialisé dans `app.py`

### Erreur: "No model run found"
- Vous devez d'abord insérer des données (Étape 5)
- Puis lancer un calcul: `POST /api/snb/model/run`

### Erreur: "OpenAI not configured"
- Vérifiez la variable `OPENAI_API_KEY`
- Si vous n'avez pas OpenAI, l'explication ne sera pas disponible (mais le modèle fonctionne quand même)

### Les charts ne s'affichent pas
- Vérifiez que Chart.js est bien chargé (via CDN dans le template)
- Ouvrez la console développeur (F12) pour voir les erreurs JS

---

## 📚 Structure des fichiers créés

```
inventorysbo/
├── create_snb_tables.sql          # Script SQL Supabase
├── snb_policy_engine.py           # Moteur de calcul du modèle
├── snb_routes.py                  # Routes Flask (API)
├── templates/
│   └── snb_taux.html              # Template HTML frontend
└── static/
    └── js/
        └── snb_taux.js            # JavaScript frontend (charts)
```

---

## 🚀 Prochaines étapes (optionnel)

### A) Intégrer ScrapingBee pour l'ingestion automatique
- Configurer des scrapers pour OFS, KOF, SNB, Eurex
- Automatiser les POST vers `/api/snb/ingest/*`

### B) Ajouter le NEER (taux de change effectif nominal)
- Source: data.snb.ch
- Endpoint: `/api/snb/ingest/neer`

### C) Scheduler les mises à jour
- Hebdo: OIS/NEER
- Mensuel: CPI/KOF
- Trimestriel: MPA BNS

### D) Alertes et notifications
- Si |règle - marché| > 40 bps → alerte email
- Dashboard temps réel

---

## ✅ Checklist finale

- [ ] Tables Supabase créées
- [ ] Fichiers Python créés (snb_policy_engine.py, snb_routes.py)
- [ ] Template HTML créé (snb_taux.html)
- [ ] JavaScript créé (snb_taux.js)
- [ ] app.py modifié (import, config, blueprint, route)
- [ ] index.html modifié (lien menu)
- [ ] Application redémarrée
- [ ] Données de test insérées
- [ ] Page accessible et fonctionnelle
- [ ] Calcul du modèle fonctionne
- [ ] Explication GPT-5 fonctionne (si OpenAI configuré)

---

**Si vous avez des questions ou des erreurs, copiez le message d'erreur complet et je vous aiderai à déboguer !**

