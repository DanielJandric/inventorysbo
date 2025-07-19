# 🚀 Configuration BONVIN Collection

## 📋 Prérequis

- Python 3.8+
- Compte Supabase
- Clé API EODHD
- Clé API OpenAI

## 🔧 Configuration

### 1. Variables d'environnement

Créez un fichier `config.py` avec vos vraies clés :

```python
import os

# Supabase
os.environ['SUPABASE_URL'] = "https://votre-projet.supabase.co"
os.environ['SUPABASE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.votre_clé_supabase_ici"

# APIs
os.environ['EODHD_API_KEY'] = "votre_clé_eodhd_ici"
os.environ['OPENAI_API_KEY'] = "sk-votre_clé_openai_ici"
```

### 2. Base de données

Exécutez le script SQL dans Supabase :
```sql
-- Voir script_sql_final.sql
```

### 3. Installation

```bash
pip install -r requirements.txt
python config.py
python app.py
```

## 🎯 Fonctionnalités

- ✅ Interface moderne avec tons dorés gris
- ✅ Analytics avec Treemap D3.js
- ✅ Intégration EODHD pour métriques boursières
- ✅ Sauvegarde automatique Supabase
- ✅ Recherche sémantique OpenAI
- ✅ Rafraîchissement manuel des prix

## 🔗 URLs

- **Application** : http://localhost:5000
- **Analytics** : http://localhost:5000/analytics
- **API Health** : http://localhost:5000/health 