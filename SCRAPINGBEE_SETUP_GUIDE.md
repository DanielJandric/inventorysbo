# 🐝 Guide de Configuration ScrapingBee

## Vue d'ensemble

ScrapingBee est un service de web scraping professionnel qui offre plusieurs avantages par rapport à Playwright :

### ✅ Avantages de ScrapingBee

1. **Pas de gestion de navigateur** - Plus simple à déployer
2. **Anti-détection intégrée** - Évite les blocages automatiquement
3. **API REST simple** - Plus fiable que Playwright
4. **Gestion des proxies** - Rotation automatique
5. **Moins de ressources** - Pas besoin de navigateur complet
6. **Plan gratuit** - 1000 requêtes/mois

### 🔄 Comparaison avec Playwright

| Fonctionnalité | Playwright | ScrapingBee |
|----------------|------------|-------------|
| Complexité | Élevée | Faible |
| Ressources | Élevées | Faibles |
| Anti-détection | Manuel | Automatique |
| Déploiement | Complexe | Simple |
| Coût | Gratuit | Payant après quota |

## 🚀 Installation et Configuration

### Étape 1: Obtenir une clé API ScrapingBee

1. Allez sur [https://www.scrapingbee.com/](https://www.scrapingbee.com/)
2. Créez un compte gratuit
3. Obtenez votre clé API dans le dashboard
4. Notez votre clé API

### Étape 2: Configuration automatique

```bash
python configure_scrapingbee.py
```

### Étape 3: Configuration manuelle

Ajoutez votre clé API dans le fichier `.env` :

```env
SCRAPINGBEE_API_KEY=votre_cle_api_ici
```

## 🧪 Test de la Configuration

### Test automatique

```bash
python test_scrapingbee_scraper.py
```

### Test manuel

```python
from scrapingbee_scraper import get_scrapingbee_scraper
import asyncio

async def test():
    scraper = get_scrapingbee_scraper()
    scraper.initialize_sync()
    
    task_id = await scraper.create_scraping_task("Tesla stock price", 3)
    result = await scraper.execute_scraping_task(task_id)
    
    print(result)

asyncio.run(test())
```

## 🌐 Interface Web

### Accès à l'interface

```
http://localhost:5000/scrapingbee-scraper
```

### Fonctionnalités de l'interface

- ✅ Statut du scraper en temps réel
- ✅ Configuration des paramètres de recherche
- ✅ Actions rapides pour les actions populaires
- ✅ Affichage des résultats structurés
- ✅ Métriques de performance

## 📡 API Endpoints

### Statut général

```http
GET /api/scrapingbee/status
```

### Créer et exécuter une tâche

```http
POST /api/scrapingbee/scrape
Content-Type: application/json

{
    "prompt": "Tesla stock price today",
    "num_results": 5
}
```

### Statut d'une tâche

```http
GET /api/scrapingbee/status/{task_id}
```

### Exécuter une tâche

```http
POST /api/scrapingbee/execute/{task_id}
```

## 🔧 Configuration Avancée

### Paramètres ScrapingBee

Le scraper utilise les paramètres suivants par défaut :

```python
params = {
    'api_key': self.api_key,
    'url': url,
    'render_js': 'true',  # Rendu JavaScript
    'premium_proxy': 'true',  # Proxy premium
    'country_code': 'us',  # Proxy US
    'extract_rules': json.dumps({
        'title': {'selector': 'title', 'type': 'text'},
        'content': {'selector': 'body', 'type': 'text'}
    })
}
```

### Personnalisation

Vous pouvez modifier ces paramètres dans `scrapingbee_scraper.py` :

```python
# Dans la méthode _scrape_page
params = {
    'api_key': self.api_key,
    'url': url,
    'render_js': 'true',
    'premium_proxy': 'true',
    'country_code': 'us',  # Changer le pays
    'custom_google': 'true',  # Utiliser Google personnalisé
    'extract_rules': json.dumps({
        # Personnaliser les règles d'extraction
    })
}
```

## 📊 Utilisation dans l'Application

### Intégration avec Flask

Le ScrapingBee scraper est intégré dans l'application Flask :

```python
# Initialisation
scrapingbee_scraper_manager = get_scrapingbee_scraper()
scrapingbee_scraper_manager.initialize_sync()

# Utilisation
task_id = await scrapingbee_scraper_manager.create_scraping_task(prompt, num_results)
result = await scrapingbee_scraper_manager.execute_scraping_task(task_id)
```

### Remplacement de Playwright

Pour utiliser ScrapingBee au lieu de Playwright :

```python
# Au lieu de
from intelligent_scraper import IntelligentScraper

# Utilisez
from scrapingbee_scraper import ScrapingBeeScraper
```

## 🚨 Dépannage

### Erreurs courantes

1. **"SCRAPINGBEE_API_KEY requis"**
   - Vérifiez que la clé API est dans le fichier `.env`
   - Relancez l'application après modification

2. **"API key not valid"**
   - Vérifiez votre clé API sur le dashboard ScrapingBee
   - Assurez-vous que votre compte est actif

3. **"Quota exceeded"**
   - Vérifiez votre quota sur le dashboard ScrapingBee
   - Considérez un plan payant pour plus de requêtes

4. **"No results found"**
   - Vérifiez votre connexion internet
   - Essayez avec un prompt différent
   - Vérifiez que le site cible n'est pas bloqué

### Logs de débogage

Activez les logs détaillés :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 💰 Coûts et Quotas

### Plan gratuit
- 1000 requêtes/mois
- Proxy premium inclus
- Support communautaire

### Plans payants
- Starter: $49/mois - 50,000 requêtes
- Business: $199/mois - 250,000 requêtes
- Enterprise: Sur mesure

## 🔗 Ressources

- [Site web ScrapingBee](https://www.scrapingbee.com/)
- [Documentation API](https://www.scrapingbee.com/docs/)
- [Dashboard](https://app.scrapingbee.com/)
- [Support](https://www.scrapingbee.com/support/)

## 📝 Notes importantes

1. **Respectez les robots.txt** - ScrapingBee respecte automatiquement les robots.txt
2. **Rate limiting** - Le service gère automatiquement les limites de taux
3. **Données personnelles** - ScrapingBee ne collecte pas de données personnelles
4. **Conformité** - Vérifiez la conformité avec les sites que vous scrapez

## 🎯 Prochaines étapes

1. Configurez votre clé API ScrapingBee
2. Testez l'interface web
3. Intégrez dans vos workflows existants
4. Surveillez votre utilisation et coûts
5. Optimisez vos requêtes pour réduire les coûts 