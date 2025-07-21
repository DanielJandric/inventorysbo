# 🚀 Guide de Configuration Gemini

## Vue d'ensemble

Gemini est utilisé dans l'application pour générer des briefings de marché automatiques avec recherche web en temps réel. Cette fonctionnalité remplace l'ancienne méthode basée sur OpenAI pour les mises à jour de marché.

## 🔧 Configuration

### 1. Obtenir une clé API Gemini

1. **Accédez à Google AI Studio**
   - Allez sur [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - Connectez-vous avec votre compte Google

2. **Créer un projet**
   - Cliquez sur "Create API Key"
   - Sélectionnez un projet existant ou créez-en un nouveau
   - Copiez la clé API générée

3. **Format de la clé**
   - Les clés Gemini commencent par `AIzaSy`
   - Exemple: `AIzaSyABC123DEF456GHI789JKL012MNO345PQR678STU`

### 2. Configuration locale

#### Option A: Fichier .env
```bash
# Créer ou modifier le fichier .env
echo "GEMINI_API_KEY=votre_clé_gemini_ici" >> .env
```

#### Option B: Fichier config.py
```python
# Dans config.py
os.environ['GEMINI_API_KEY'] = "votre_clé_gemini_ici"
```

### 3. Configuration Render (Production)

Dans le dashboard Render de votre application :

1. Allez dans **Environment Variables**
2. Ajoutez la variable :
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Votre clé Gemini

## 🧪 Test de la Configuration

### Test local
```bash
python test_gemini_api.py
```

### Test via l'application
1. Lancez l'application : `python app.py`
2. Allez sur `/markets`
3. Cliquez sur "Générer Update"
4. Vérifiez les logs pour les messages Gemini

## 🔍 Fonctionnalités Gemini

### Briefing de Marché Automatique
- **Génération quotidienne** à 21h30 CEST
- **Recherche web en temps réel** pour données actuelles
- **Structure complète** : Actions, Obligations, Crypto, Macro
- **Notifications email** automatiques

### Déclenchement Manuel
- **Bouton "Générer Update"** sur la page Markets
- **Données actuelles** via recherche web
- **Format narratif** structuré

## 📊 Structure du Briefing

Le briefing généré par Gemini inclut :

1. **MARCHÉS ACTIONS**
   - USA (S&P 500, NASDAQ, Dow Jones)
   - Europe (CAC 40, DAX, FTSE 100)
   - Suisse (SMI)
   - Autres zones si mouvement significatif

2. **OBLIGATIONS SOUVERAINES**
   - US 10Y, Bund, OAT, BTP
   - Confédération suisse
   - Spreads et mouvements

3. **CRYPTOACTIFS**
   - BTC, ETH
   - Capitalisation globale
   - Mouvements liés à la régulation ou aux flux

4. **MACROÉCONOMIE & BANQUES CENTRALES**
   - Statistiques importantes
   - Commentaires des banquiers centraux
   - Tensions géopolitiques

5. **RÉSUMÉ & POINTS DE SURVEILLANCE**
   - Bullet points clairs
   - Signaux faibles ou ruptures de tendance à surveiller

## 🛠 Dépannage

### Erreur "GEMINI_API_KEY non configurée"
```bash
# Vérifiez que la variable est définie
echo $GEMINI_API_KEY

# Ou dans Python
import os
print(os.getenv('GEMINI_API_KEY'))
```

### Erreur "Invalid API Key"
- Vérifiez que la clé commence par `AIzaSy`
- Assurez-vous que la clé est complète (pas de caractères manquants)
- Vérifiez que le projet Google Cloud est actif

### Erreur "Quota exceeded"
- Les clés Gemini gratuites ont des limites
- Considérez une mise à niveau vers un plan payant
- Ou utilisez OpenAI comme fallback

### Erreur de connectivité
```bash
# Test de connectivité
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent" \
  -H "Content-Type: application/json" \
  -H "X-goog-api-key: VOTRE_CLE" \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}'
```

## 🔄 Fallback vers OpenAI

Si Gemini n'est pas configuré ou en erreur, l'application utilise automatiquement OpenAI GPT-4o comme fallback pour les briefings de marché.

## 📈 Avantages de Gemini

### ✅ Recherche Web Intégrée
- Données en temps réel via Google Search
- Pas besoin de configurer des APIs boursières séparées
- Actualités macro et géopolitiques incluses

### ✅ Performance
- Modèle Gemini 1.5 Flash optimisé
- Réponse rapide (< 10 secondes)
- Gestion automatique des erreurs

### ✅ Coût
- Clés gratuites disponibles
- Limites généreuses pour usage personnel
- Pas de coût par requête (dans les limites)

## 🎯 Utilisation

### Génération Automatique
- **Horaire** : 21h30 CEST quotidiennement
- **Sauvegarde** : Stockage en base de données
- **Notifications** : Email automatique aux destinataires

### Génération Manuelle
- **Interface** : Page `/markets`
- **Bouton** : "Générer Update"
- **Temps réel** : Données actuelles via recherche web

## 📝 Logs et Monitoring

### Logs de l'application
```python
# Dans app.py, les logs Gemini incluent :
logger.info("✅ Briefing généré avec Gemini 1.5 Flash + Google Search")
logger.error(f"Erreur API Gemini: {response.status_code} - {response.text}")
```

### Monitoring via /health
```bash
curl https://inventorysbo.onrender.com/health
```

La réponse inclut le statut des services, y compris Gemini.

## 🔗 Ressources

- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [Documentation Gemini API](https://ai.google.dev/docs)
- [Limites et quotas](https://ai.google.dev/pricing)
- [Modèles disponibles](https://ai.google.dev/models) 