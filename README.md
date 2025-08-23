# 🚀 GPT-5 Responses API - Production

API Flask sécurisée pour GPT-5 avec extraction robuste de texte et fallback automatique.

## 🎯 Fonctionnalités

- ✅ **API Responses GPT-5** avec gestion automatique du contexte
- ✅ **Helper robuste** d'extraction de texte
- ✅ **Fallback automatique** vers Chat Completions
- ✅ **Variables d'environnement sécurisées**
- ✅ **Tests complets** (23 tests)
- ✅ **Prêt pour la production**

## 🔐 Sécurité

⚠️ **IMPORTANT**: La clé OpenAI est protégée par les variables d'environnement et n'est jamais exposée dans le code.

## 🚀 Déploiement sur Render

### 1. Variables d'environnement à configurer sur Render :

```bash
OPENAI_API_KEY=your_openai_api_key_here  # ⚠️ REQUIS - À configurer dans Render Dashboard
AI_MODEL=gpt-5
AI_COMPLETIONS_MODEL=gpt-5-chat-latest
AI_MODEL_FALLBACK=gpt-4o
MAX_OUTPUT_TOKENS=800
TIMEOUT_S=60
FALLBACK_CHAT=1
FLASK_ENV=production
FLASK_DEBUG=False
```

### 2. Instructions de déploiement :

1. **Connecter votre repo GitHub** à Render
2. **Configurer les variables d'environnement** dans le dashboard Render
3. **Déployer** - Render utilisera automatiquement `render.yaml`

### 3. Configuration automatique :

Le fichier `render.yaml` configure automatiquement :
- Service web Python
- Commande de build : `pip install -r requirements.txt`
- Commande de start : `python flask_gpt5_integration_final.py`
- Health check : `/api/gpt5/health`

## 📋 Endpoints API

### 🤖 Chat Principal
```bash
POST /api/gpt5/chat

{
  "message": "Analysez les tendances du marché boursier",
  "system_prompt": "Tu es un analyste financier expert",
  "context": "Contexte additionnel optionnel"
}
```

### 🏥 Health Check
```bash
GET /api/gpt5/health
```

### 🧪 Test Simple
```bash
POST /api/gpt5/test
```

## 🔧 Développement Local

```bash
# 1. Cloner le repo
git clone <your-repo>
cd <your-repo>

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos vraies valeurs

# 4. Lancer l'API
python flask_gpt5_integration_final.py

# 5. Tester
curl -X POST http://localhost:5000/api/gpt5/test
```

## 🧪 Tests

```bash
# Lancer tous les tests
python -m pytest tests/ -v

# Test spécifique du helper
python -m pytest tests/test_gpt5_text_extractor_helper.py -v
```

## 🏗️ Architecture

```
📁 Project Structure
├── 🚀 flask_gpt5_integration_final.py  # API Flask principale
├── 🤖 gpt5_responses_final_with_helper.py  # Gestionnaire GPT-5
├── 🔧 gpt5_text_extractor_helper.py  # Helper d'extraction robuste
├── 🧪 tests/test_gpt5_text_extractor_helper.py  # Tests complets
├── 📋 requirements.txt  # Dépendances Python
├── ⚙️ render.yaml  # Configuration Render
├── 🐳 Dockerfile  # Configuration Docker
└── 🔐 .gitignore  # Sécurité (exclut .env)
```

## 📊 Monitoring

- **Health Check** : `GET /api/gpt5/health`
- **Logs** : Consultables dans le dashboard Render
- **Metrics** : Temps de réponse et succès/échecs trackés

## 🆘 Support

En cas de problème :
1. Vérifier les logs Render
2. Tester le health check
3. Vérifier les variables d'environnement