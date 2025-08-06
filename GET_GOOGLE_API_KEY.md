# 🔑 Obtenir votre Clé API Google - Guide Rapide

## ✅ Votre Search Engine ID est déjà configuré !

Votre Search Engine ID `0426c6b27374b4a72` est maintenant configuré dans le fichier `.env`.

## 🚀 Étape suivante : Obtenir la Clé API

### 1. **Aller sur Google Cloud Console**
- Ouvrez : https://console.cloud.google.com/
- Connectez-vous avec votre compte Google

### 2. **Créer ou sélectionner un projet**
- Cliquez sur "Select a project" en haut à gauche
- Si vous n'avez pas de projet, cliquez sur "New Project"
- Nommez-le (ex: "Financial Markets Search")
- Cliquez sur "Create"

### 3. **Activer l'API Custom Search**
- Dans le menu de gauche, allez dans "APIs & Services" > "Library"
- Recherchez "Custom Search API"
- Cliquez sur "Custom Search API"
- Cliquez sur "Enable"

### 4. **Créer une clé API**
- Dans le menu de gauche, allez dans "APIs & Services" > "Credentials"
- Cliquez sur "Create Credentials" > "API Key"
- Votre clé API apparaît (elle ressemble à `AIzaSyC...`)
- **Copiez cette clé !**

### 5. **Configurer la clé dans votre projet**
- Ouvrez le fichier `.env` dans votre projet
- Remplacez `your_google_search_api_key_here` par votre clé API
- Sauvegardez le fichier

### 6. **Tester la configuration**
```bash
python test_google_search_quick.py
```

## 🔍 Vérification Rapide

Votre fichier `.env` devrait ressembler à ceci :
```bash
# Configuration Google Search API
GOOGLE_SEARCH_API_KEY=AIzaSyC...votre_clé_ici
GOOGLE_SEARCH_ENGINE_ID=0426c6b27374b4a72
```

## 🧪 Test Immédiat

Une fois la clé configurée, testez avec :
```bash
python test_google_search_quick.py
```

Vous devriez voir :
```
✅ API Google Search fonctionnelle!
📊 Résultats trouvés: [nombre]
```

## 🚨 Problèmes Courants

### **"API key not valid"**
- Vérifiez que l'API Custom Search est activée
- Assurez-vous que la clé est correctement copiée

### **"Search engine not found"**
- Votre Search Engine ID est déjà correct : `0426c6b27374b4a72`

### **"Quota exceeded"**
- Google Search API a 100 requêtes gratuites/jour
- Suffisant pour les tests

## 📞 Aide

Si vous avez des problèmes :
1. Vérifiez que l'API Custom Search est activée
2. Vérifiez que la clé API est correcte
3. Testez avec le script de test

---

**Status:** ✅ Search Engine ID configuré
**Prochaine étape:** Obtenir la clé API Google 