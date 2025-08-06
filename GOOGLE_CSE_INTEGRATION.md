# 🔍 Google CSE Integration - Documentation Complète

## 📋 Vue d'Ensemble

L'intégration Google Custom Search Engine (CSE) permet d'utiliser votre moteur de recherche personnalisé `0426c6b27374b4a72` pour effectuer des recherches financières et de marché en temps réel.

## 🏗️ Architecture

### **Composants Principaux**

1. **`google_cse_integration.py`** - Module principal d'intégration
2. **`templates/google_cse.html`** - Interface web de test
3. **Endpoints API** - Intégrés dans `app.py`
4. **Scripts de test** - `test_google_cse_integration.py`

### **Configuration**

```python
# Search Engine ID configuré
ENGINE_ID = "0426c6b27374b4a72"

# Variables d'environnement requises
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=0426c6b27374b4a72
```

## 🚀 Fonctionnalités

### **1. Recherche Générale**
```python
from google_cse_integration import GoogleCSEIntegration

cse = GoogleCSEIntegration()
response = cse.search("AAPL stock price today")
```

### **2. Recherche de Prix d'Actions**
```python
price_data = cse.search_stock_price("AAPL")
# Retourne: {'symbol': 'AAPL', 'price': '150.25', 'source': '...', 'confidence': 0.8}
```

### **3. Nouvelles du Marché**
```python
news = cse.search_market_news(["stock market", "financial news"])
# Retourne une liste d'articles avec titre, contenu, URL
```

### **4. Briefing du Marché**
```python
briefing = cse.search_market_briefing("global")
# Retourne un briefing structuré avec sources
```

## 🌐 Interface Web

### **Accès**
```
http://localhost:5000/google-cse
```

### **Fonctionnalités de l'Interface**

1. **Status Panel** - Vérification de la configuration
2. **Search Panel** - Recherche personnalisée
3. **Results Panel** - Affichage des résultats
4. **Quick Actions** - Actions rapides prédéfinies
5. **CSE Widget** - Widget Google CSE intégré

## 🔌 API Endpoints

### **1. Status**
```http
GET /api/google-cse/status
```

**Réponse:**
```json
{
  "status": "operational",
  "engine_id": "0426c6b27374b4a72",
  "api_key_configured": true,
  "base_url": "https://www.googleapis.com/customsearch/v1"
}
```

### **2. Recherche**
```http
POST /api/google-cse/search
Content-Type: application/json

{
  "query": "AAPL stock price today"
}
```

**Réponse:**
```json
{
  "success": true,
  "results": [
    {
      "title": "Apple Stock Price Today",
      "link": "https://...",
      "snippet": "Apple Inc. stock price...",
      "source": "Google CSE"
    }
  ],
  "total_results": 1000,
  "search_time": 0.5,
  "query": "AAPL stock price today"
}
```

### **3. Prix d'Actions**
```http
GET /api/google-cse/stock-price/AAPL
```

**Réponse:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "price": "150.25",
    "source": "https://...",
    "confidence": 0.8,
    "currency": "USD"
  }
}
```

### **4. Nouvelles du Marché**
```http
POST /api/google-cse/market-news
Content-Type: application/json

{
  "keywords": ["stock market", "financial news"]
}
```

### **5. Briefing du Marché**
```http
POST /api/google-cse/market-briefing
Content-Type: application/json

{
  "location": "global"
}
```

## 🧪 Tests

### **Test Complet**
```bash
python test_google_cse_integration.py
```

### **Test Rapide**
```bash
python google_cse_integration.py
```

### **Test via Interface Web**
1. Démarrez l'application: `python app.py`
2. Accédez à: `http://localhost:5000/google-cse`
3. Utilisez les boutons "Actions Rapides"

## 📊 Métriques et Performance

### **Limites Google CSE**
- **Gratuit:** 100 requêtes/jour
- **Payant:** $5 pour 1000 requêtes
- **Limite par requête:** 10 résultats maximum

### **Optimisations**
- Cache des résultats
- Extraction intelligente des prix
- Fallback vers d'autres sources
- Gestion des erreurs robuste

## 🔧 Configuration

### **1. Obtenir la Clé API**
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un projet ou sélectionnez un existant
3. Activez l'API Custom Search Engine
4. Créez une clé API dans "Credentials"

### **2. Configurer les Variables**
```bash
# Dans votre fichier .env
GOOGLE_SEARCH_API_KEY=AIzaSyC...votre_clé_ici
GOOGLE_SEARCH_ENGINE_ID=0426c6b27374b4a72
```

### **3. Vérifier la Configuration**
```bash
python check_config.py
```

## 🚨 Dépannage

### **Erreurs Courantes**

#### **"API key not valid"**
- Vérifiez que l'API Custom Search est activée
- Assurez-vous que la clé est correctement copiée
- Vérifiez les quotas dans Google Cloud Console

#### **"Search engine not found"**
- Votre Search Engine ID est correct: `0426c6b27374b4a72`
- Vérifiez que le moteur est configuré pour rechercher sur tout le web

#### **"Quota exceeded"**
- Google CSE a 100 requêtes gratuites/jour
- Consultez votre quota dans Google Cloud Console
- Considérez l'utilisation d'un compte payant

### **Logs et Debug**
```bash
# Voir les logs détaillés
python app.py

# Tester la configuration
python test_google_cse_integration.py

# Vérifier le status
curl http://localhost:5000/api/google-cse/status
```

## 🔄 Intégration avec le Système Existant

### **Unified Market Manager**
L'intégration Google CSE est disponible dans le gestionnaire unifié :
- Priorité: Google CSE → OpenAI Web Search → Manus API
- Cache partagé
- Interface unifiée

### **Fallback System**
```python
# Dans unified_market_manager.py
def get_stock_price(self, symbol: str):
    # 1. Essayer Google CSE
    # 2. Fallback vers OpenAI Web Search
    # 3. Fallback vers Manus API
```

## 📈 Utilisation Avancée

### **Recherche Personnalisée**
```python
# Recherche avec paramètres avancés
response = cse.search(
    query="TSLA stock price",
    num_results=5,
    date_restrict="d1"  # Dernières 24h
)
```

### **Extraction de Prix**
```python
# Extraction automatique des prix
price = cse._extract_price("Apple stock is trading at $150.25")
# Retourne: "150.25"
```

### **Briefing Personnalisé**
```python
# Briefing pour une localisation spécifique
briefing = cse.search_market_briefing("Europe")
```

## 🔒 Sécurité

### **Restrictions de Clé API**
1. Dans Google Cloud Console, allez dans "APIs & Services" > "Credentials"
2. Cliquez sur votre clé API
3. Dans "Application restrictions", sélectionnez "HTTP referrers"
4. Ajoutez vos domaines autorisés

### **Variables d'Environnement**
- Ne jamais commiter les clés API dans le code
- Utiliser des variables d'environnement
- Protéger le fichier `.env`

## 📞 Support

### **Documentation Officielle**
- [Google Custom Search API](https://developers.google.com/custom-search)
- [Google Cloud Console](https://console.cloud.google.com/)

### **Aide Locale**
```bash
# Vérifier la configuration
python check_config.py

# Tester l'intégration
python test_google_cse_integration.py

# Voir les logs
python app.py
```

### **Fichiers de Configuration**
- `google_cse_integration.py` - Module principal
- `templates/google_cse.html` - Interface web
- `test_google_cse_integration.py` - Tests complets
- `.env` - Variables d'environnement

---

**Status:** ✅ Intégration complète
**Search Engine ID:** 0426c6b27374b4a72
**Dernière mise à jour:** 2025-08-06 