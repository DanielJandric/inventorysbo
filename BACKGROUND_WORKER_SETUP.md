# 🚀 Guide de Configuration du Background Worker

## 📋 Prérequis

1. **Compte Render** avec accès aux Background Workers
2. **Dépôt Git** connecté à votre projet
3. **Variables d'environnement** configurées

## 🔧 Configuration sur Render

### 1. Créer le Background Worker

1. Allez sur votre [Dashboard Render](https://dashboard.render.com)
2. Cliquez sur **"New +"** → **"Background Worker"**
3. Connectez-le au même dépôt Git que votre application web
4. Nommez-le : `market-analysis-worker`

### 2. Configuration du Service

#### **Build Command :**
```bash
pip install -r requirements.txt
```

#### **Start Command :**
```bash
python background_worker.py
```

#### **Variables d'Environnement :**
```
SCRAPINGBEE_API_KEY=votre_clé_scrapingbee_ici
OPENAI_API_KEY=votre_clé_openai_ici
```

### 3. Configuration Avancée

#### **Plan :**
- **Free** : Pour les tests
- **Starter** : Pour la production (recommandé)

#### **Auto-Deploy :**
- ✅ **Activé** : Déploiement automatique sur push

## 📊 Fonctionnement

### Boucle d'Exécution
```
Démarrage → Initialisation → Analyse → Pause (4h) → Répétition
```

### Logs Disponibles
- **Initialisation** : Vérification des variables d'environnement
- **Analyse** : Progression du scraping et traitement IA
- **Statistiques** : Nombre de points clés, insights, etc.
- **Erreurs** : Gestion automatique des erreurs avec retry

### Intervalles Configurables
- **Analyse de marché** : 4 heures (configurable dans `worker_config.py`)
- **Retry en cas d'erreur** : 1 heure
- **Vérification de santé** : 30 minutes

## 🧪 Test Local

### Test Rapide
```bash
python test_background_worker.py
```

### Test Complet
```bash
python background_worker.py
```

## 📈 Monitoring

### Logs Render
- Accédez aux logs via le dashboard Render
- Filtrez par niveau : INFO, WARNING, ERROR

### Métriques
- **Succès** : Nombre d'analyses réussies
- **Erreurs** : Types d'erreurs et fréquence
- **Performance** : Temps d'exécution par analyse

## 🔄 Maintenance

### Redémarrage
- Via le dashboard Render : "Manual Deploy"
- Ou redémarrage automatique en cas d'erreur

### Mise à Jour
- Push sur Git → Déploiement automatique
- Ou déploiement manuel via dashboard

### Configuration
- Modifiez `worker_config.py` pour ajuster les paramètres
- Redéployez pour appliquer les changements

## 🚨 Dépannage

### Erreurs Communes

#### **Variables d'environnement manquantes**
```
❌ Variables d'environnement manquantes: SCRAPINGBEE_API_KEY
```
**Solution :** Vérifiez les variables dans Render Dashboard

#### **Timeout de scraping**
```
❌ Erreur ScrapingBee scraping: 408
```
**Solution :** Le worker continue automatiquement après 1 heure

#### **Erreur OpenAI**
```
❌ Erreur traitement LLM: Invalid API key
```
**Solution :** Vérifiez la clé OpenAI dans les variables d'environnement

### Logs Utiles
```bash
# Vérifier les logs en temps réel
tail -f /var/log/background-worker.log

# Filtrer les erreurs
grep "ERROR" /var/log/background-worker.log
```

## ✅ Checklist de Déploiement

- [ ] Background Worker créé sur Render
- [ ] Variables d'environnement configurées
- [ ] Start Command : `python background_worker.py`
- [ ] Build Command : `pip install -r requirements.txt`
- [ ] Auto-deploy activé
- [ ] Test local réussi
- [ ] Premier déploiement réussi
- [ ] Logs vérifiés
- [ ] Première analyse réussie

## 🎯 Avantages du Background Worker

✅ **Pas de timeout** : Exécution illimitée
✅ **Automatisation** : Analyses régulières
✅ **Robustesse** : Gestion d'erreurs automatique
✅ **Monitoring** : Logs détaillés
✅ **Scalabilité** : Facilement extensible
✅ **Coût** : Gratuit pour les tests, abordable pour la production

## 📞 Support

En cas de problème :
1. Vérifiez les logs Render
2. Testez localement avec `test_background_worker.py`
3. Vérifiez les variables d'environnement
4. Consultez la documentation Render 