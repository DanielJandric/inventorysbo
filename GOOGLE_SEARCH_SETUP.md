# 🔧 Configuration Google Search API - Guide Rapide

## ⚠️ Problème Actuel

Vous voyez ces avertissements :
```
WARNING:google_search_manager:⚠️ Configuration Google Search manquante
WARNING:app:⚠️ Gestionnaire de recherche Google non disponible (configuration manquante)
```

Cela signifie que les variables d'environnement Google Search ne sont pas configurées.

## 🚀 Solution Rapide

### Étape 1: Obtenir les Clés API

#### **1. Créer un projet Google Cloud**
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Cliquez sur "Select a project" > "New Project"
3. Nommez votre projet (ex: "Financial Markets Search")
4. Cliquez sur "Create"

#### **2. Activer l'API Custom Search**
1. Dans votre projet, allez dans "APIs & Services" > "Library"
2. Recherchez "Custom Search API"
3. Cliquez sur "Custom Search API" > "Enable"

#### **3. Créer une clé API**
1. Allez dans "APIs & Services" > "Credentials"
2. Cliquez sur "Create Credentials" > "API Key"
3. Copiez la clé API (elle ressemble à `AIzaSyC...`)

#### **4. Créer un Custom Search Engine**
1. Allez sur [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Cliquez sur "Create a search engine"
3. Configurez :
   - **Sites to search:** Laissez vide (pour rechercher sur tout le web)
   - **Name:** "Financial Markets Search"
   - **Description:** "Search engine for financial markets"
4. Cliquez sur "Create"
5. Notez l'ID du moteur (il ressemble à `012345678901234567890:abcdefghijk`)

### Étape 2: Configurer les Variables d'Environnement

#### **Option A: Fichier .env**
Créez un fichier `.env` à la racine du projet :

```bash
# Configuration Google Search API
GOOGLE_SEARCH_API_KEY=AIzaSyC...votre_clé_api_ici
GOOGLE_SEARCH_ENGINE_ID=012345678901234567890:abcdefghijk

# Autres configurations...
OPENAI_API_KEY=votre_openai_api_key
SUPABASE_URL=votre_supabase_url
SUPABASE_KEY=votre_supabase_key
```

#### **Option B: Variables d'Environnement Système**

**Windows (PowerShell):**
```powershell
$env:GOOGLE_SEARCH_API_KEY="AIzaSyC...votre_clé_api_ici"
$env:GOOGLE_SEARCH_ENGINE_ID="012345678901234567890:abcdefghijk"
```

**Linux/Mac:**
```bash
export GOOGLE_SEARCH_API_KEY="AIzaSyC...votre_clé_api_ici"
export GOOGLE_SEARCH_ENGINE_ID="012345678901234567890:abcdefghijk"
```

### Étape 3: Tester la Configuration

Exécutez le script de test :

```bash
python setup_google_search.py
```

Vous devriez voir :
```
✅ API Key: Configurée
✅ Search Engine ID: Configuré
✅ API Google Search fonctionnelle
✅ Gestionnaire unifié: operational
```

## 🔍 Vérification

### Test Manuel

```bash
# Test de l'API Google Search
curl "https://www.googleapis.com/customsearch/v1?key=VOTRE_API_KEY&cx=VOTRE_ENGINE_ID&q=AAPL+stock+price&num=1"
```

### Test via l'Interface Web

1. Démarrez l'application :
   ```bash
   python app.py
   ```

2. Accédez à l'interface unifiée :
   ```
   http://localhost:5000/unified-market
   ```

3. Testez la recherche de prix d'actions

## 🚨 Problèmes Courants

### **Erreur: "API key not valid"**
- Vérifiez que la clé API est correcte
- Assurez-vous que l'API Custom Search est activée
- Vérifiez les quotas de votre projet Google Cloud

### **Erreur: "Search engine not found"**
- Vérifiez que l'ID du moteur de recherche est correct
- Assurez-vous que le moteur de recherche est configuré pour rechercher sur tout le web

### **Erreur: "Quota exceeded"**
- Google Search API a des limites de requêtes
- Consultez votre quota dans Google Cloud Console
- Considérez l'utilisation d'un compte payant pour plus de requêtes

## 📊 Quotas et Limites

### **Gratuit (100 requêtes/jour)**
- Suffisant pour les tests et développement
- Limite par projet Google Cloud

### **Payant**
- $5 pour 1000 requêtes
- Limites plus élevées
- Support prioritaire

## 🔒 Sécurité

### **Restrictions de Clé API**
1. Dans Google Cloud Console, allez dans "APIs & Services" > "Credentials"
2. Cliquez sur votre clé API
3. Dans "Application restrictions", sélectionnez "HTTP referrers"
4. Ajoutez vos domaines autorisés

### **Restrictions d'API**
1. Dans "APIs & Services" > "OAuth consent screen"
2. Configurez les domaines autorisés
3. Limitez l'accès aux APIs nécessaires

## 📞 Support

### **Documentation Officielle**
- [Google Custom Search API](https://developers.google.com/custom-search)
- [Google Cloud Console](https://console.cloud.google.com/)

### **Aide Locale**
```bash
# Vérifier la configuration
python setup_google_search.py

# Tester le gestionnaire unifié
python test_unified_market_manager.py

# Voir les logs détaillés
python app.py
```

---

**Status:** ✅ Guide de configuration complet
**Dernière mise à jour:** 2025-08-06 