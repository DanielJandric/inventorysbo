# 🚀 Configuration BONVIN Collection

## 📋 Prérequis

- Python 3.8+
- Compte Supabase
- Clé API EODHD
- Clé API OpenAI

## 🔧 Configuration

### 1. Variables d'environnement

#### Pour le développement local :
Copiez `config_example.py` en `config.py` et remplacez par vos vraies clés :

```bash
copy config_example.py config.py
# Puis éditez config.py avec vos vraies clés
```

#### Pour le déploiement (Render/Vercel) :
Les variables d'environnement sont définies dans le dashboard du service.

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