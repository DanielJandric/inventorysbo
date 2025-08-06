# Google Search API Implementation

## Vue d'ensemble

Cette implémentation ajoute une intégration complète avec l'API Google Custom Search pour fournir des rapports de marché et des nouvelles quotidiennes en temps réel pour le système d'informations financières.

## Fonctionnalités

### 🔍 Recherche Google Custom Search
- **Sources fiables**: Intégration avec des sources financières reconnues (Reuters, Bloomberg, CNBC, etc.)
- **Types de recherche**: 7 types spécialisés (marchés, crypto, forex, commodités, etc.)
- **Filtrage intelligent**: Tri par pertinence et date de publication
- **Scores de pertinence**: Algorithme de scoring pour prioriser les résultats

### 📊 Rapports de Marché Quotidiens
- **Analyse multi-source**: Agrégation de plusieurs sources d'information
- **Sentiment du marché**: Analyse automatique (Bullish/Bearish/Neutral)
- **Impact évalué**: Classification de l'impact (High/Medium/Low)
- **Points clés**: Extraction automatique des informations importantes

### 📰 Nouvelles Quotidiennes
- **Catégories multiples**: Marchés, crypto, forex, commodités, actions, économie
- **Niveaux d'importance**: Classification automatique (high/medium/low)
- **Sources diversifiées**: Couverture complète des sources financières
- **Tri intelligent**: Par importance et pertinence

## Architecture

### Modules

#### `google_search_manager.py`
Module principal gérant l'intégration Google Search API.

**Classes principales:**
- `GoogleSearchManager`: Gestionnaire principal de l'API
- `GoogleSearchType`: Enum des types de recherche
- `GoogleSearchResult`: Structure des résultats de recherche
- `MarketReport`: Structure des rapports de marché
- `DailyNewsItem`: Structure des nouvelles quotidiennes

**Fonctionnalités clés:**
```python
# Initialisation
google_search_manager = create_google_search_manager()

# Recherche de marchés financiers
results = google_search_manager.search_financial_markets(
    query="market news today",
    search_type=GoogleSearchType.MARKET_NEWS,
    max_results=10,
    date_restrict="d1"
)

# Rapport de marché quotidien
report = google_search_manager.get_daily_market_report(location="global")

# Nouvelles quotidiennes
news_items = google_search_manager.get_daily_news_summary(
    categories=['market', 'crypto', 'forex']
)
```

### Intégration dans `app.py`

**Initialisation:**
```python
# Initialize Google Search Manager
google_search_manager = None
try:
    google_search_manager = create_google_search_manager()
    if google_search_manager:
        logger.info("✅ Gestionnaire de recherche Google initialisé")
    else:
        logger.warning("⚠️ Gestionnaire de recherche Google non disponible")
except Exception as e:
    logger.error(f"❌ Erreur initialisation Google Search Manager: {e}")
```

**Endpoints API:**
- `POST /api/google-search/market-report`: Génération de rapports de marché
- `POST /api/google-search/daily-news`: Récupération de nouvelles quotidiennes
- `POST /api/google-search/financial-markets`: Recherche de marchés financiers
- `GET /api/google-search/stock/<symbol>`: Recherche d'informations d'actions
- `GET /api/google-search/status`: Statut du service

## Configuration

### Variables d'environnement requises

```bash
# Google Custom Search API
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
```

### Configuration du moteur de recherche personnalisé

1. **Créer un projet Google Cloud:**
   - Aller sur [Google Cloud Console](https://console.cloud.google.com/)
   - Créer un nouveau projet ou sélectionner un existant

2. **Activer l'API Custom Search:**
   - Aller dans "APIs & Services" > "Library"
   - Rechercher "Custom Search API"
   - Activer l'API

3. **Créer des clés API:**
   - Aller dans "APIs & Services" > "Credentials"
   - Créer une nouvelle clé API
   - Copier la clé dans `GOOGLE_SEARCH_API_KEY`

4. **Configurer le moteur de recherche personnalisé:**
   - Aller sur [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
   - Créer un nouveau moteur de recherche
   - Configurer les sites à rechercher (sources financières)
   - Copier l'ID du moteur dans `GOOGLE_SEARCH_ENGINE_ID`

### Sources financières configurées

```python
financial_sources = [
    "reuters.com",
    "bloomberg.com", 
    "cnbc.com",
    "marketwatch.com",
    "yahoo.com/finance",
    "investing.com",
    "seekingalpha.com",
    "financialtimes.com",
    "wsj.com",
    "ft.com"
]
```

## Utilisation

### Interface Web

Accéder à l'interface de test: `http://localhost:5000/google-search`

**Fonctionnalités disponibles:**
- ✅ Vérification du statut du service
- 📊 Génération de rapports de marché
- 📰 Récupération de nouvelles quotidiennes
- 🔍 Recherche de marchés financiers
- 📈 Recherche d'informations d'actions

### API REST

#### 1. Statut du service
```bash
curl -X GET "http://localhost:5000/api/google-search/status"
```

#### 2. Rapport de marché
```bash
curl -X POST "http://localhost:5000/api/google-search/market-report" \
  -H "Content-Type: application/json" \
  -d '{"location": "global"}'
```

#### 3. Nouvelles quotidiennes
```bash
curl -X POST "http://localhost:5000/api/google-search/daily-news" \
  -H "Content-Type: application/json" \
  -d '{"categories": ["market", "crypto", "forex"]}'
```

#### 4. Recherche de marchés
```bash
curl -X POST "http://localhost:5000/api/google-search/financial-markets" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "market news today",
    "search_type": "market_news",
    "max_results": 10,
    "date_restrict": "d1"
  }'
```

#### 5. Recherche d'actions
```bash
curl -X GET "http://localhost:5000/api/google-search/stock/AAPL"
```

## Tests

### Script de test automatisé

Exécuter les tests complets:
```bash
python test_google_search_integration.py
```

**Tests inclus:**
- ✅ Statut de l'API
- 📊 Génération de rapports de marché
- 📰 Récupération de nouvelles quotidiennes
- 🔍 Recherche de marchés financiers
- 📈 Recherche d'actions
- 🌐 Interface web
- 🔗 Intégration système
- ⚡ Tests de performance

### Tests manuels

1. **Vérifier le statut:**
   ```bash
   curl http://localhost:5000/api/google-search/status
   ```

2. **Tester l'interface web:**
   - Ouvrir `http://localhost:5000/google-search`
   - Vérifier que tous les boutons fonctionnent

3. **Tester les endpoints:**
   - Utiliser les exemples curl ci-dessus
   - Vérifier les réponses JSON

## Algorithmes

### Score de pertinence

```python
def _calculate_relevance_score(self, item: Dict, search_type: GoogleSearchType) -> float:
    score = 0.0
    
    # Bonus pour les sources fiables (0.3)
    for source in self.financial_sources:
        if source.replace('www.', '') in link:
            score += 0.3
            break
    
    # Bonus pour les mots-clés pertinents (0.2 par titre, 0.1 par snippet)
    relevant_keywords = keywords.get(search_type, [])
    for keyword in relevant_keywords:
        if keyword in title:
            score += 0.2
        if keyword in snippet:
            score += 0.1
    
    # Bonus pour les contenus récents (0.1)
    if 'today' in title or 'today' in snippet:
        score += 0.1
    
    return min(score, 1.0)
```

### Analyse de sentiment

```python
def _analyze_market_sentiment(self, results: List[GoogleSearchResult]) -> str:
    positive_words = ['gain', 'rise', 'up', 'positive', 'bullish', 'growth', 'profit']
    negative_words = ['fall', 'drop', 'down', 'negative', 'bearish', 'loss', 'decline']
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        return "Bullish"
    elif negative_count > positive_count:
        return "Bearish"
    else:
        return "Neutral"
```

## Gestion d'erreurs

### Types d'erreurs gérées

1. **Configuration manquante:**
   - Variables d'environnement non définies
   - Clés API invalides

2. **Erreurs de réseau:**
   - Timeout de connexion
   - Erreurs HTTP

3. **Erreurs de données:**
   - Réponses JSON invalides
   - Données manquantes

### Stratégies de fallback

```python
def _create_error_report(self, error_message: str) -> MarketReport:
    return MarketReport(
        title="Erreur - Rapport de Marché",
        summary=f"Erreur lors de la génération du rapport: {error_message}",
        key_points=["Erreur de connexion à l'API Google"],
        market_sentiment="Unknown",
        sources=["Error"],
        timestamp=datetime.now().isoformat(),
        market_impact="Unknown"
    )
```

## Performance

### Optimisations

1. **Limitation des résultats:** Maximum 10 résultats par requête (limite Google)
2. **Cache intelligent:** Réutilisation des résultats récents
3. **Requêtes optimisées:** Construction de requêtes enrichies
4. **Tri efficace:** Tri par score de pertinence

### Métriques

- **Temps de réponse:** < 30 secondes pour un rapport complet
- **Précision:** Score de pertinence > 0.5 pour les résultats pertinents
- **Disponibilité:** 99%+ avec gestion d'erreurs robuste

## Sécurité

### Bonnes pratiques

1. **Clés API sécurisées:**
   - Stockage dans les variables d'environnement
   - Pas de hardcoding dans le code

2. **Validation des entrées:**
   - Validation des paramètres de requête
   - Sanitisation des données

3. **Limitation des requêtes:**
   - Respect des limites de l'API Google
   - Gestion des timeouts

## Maintenance

### Monitoring

1. **Logs détaillés:**
   ```python
   logger.info(f"🔍 Recherche Google: {enhanced_query}")
   logger.info(f"✅ {len(results)} résultats trouvés")
   logger.error(f"❌ Erreur recherche Google: {e}")
   ```

2. **Statut du service:**
   - Endpoint `/api/google-search/status`
   - Vérification de la disponibilité

### Mises à jour

1. **Sources financières:**
   - Ajout/suppression de sources dans `financial_sources`
   - Mise à jour des mots-clés par type

2. **Types de recherche:**
   - Ajout de nouveaux types dans `GoogleSearchType`
   - Configuration des mots-clés correspondants

## Dépendances

### Python
```python
import requests
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
```

### Variables d'environnement
```bash
GOOGLE_SEARCH_API_KEY=your_api_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id
```

## Support

### Dépannage

1. **Service non disponible:**
   - Vérifier les variables d'environnement
   - Tester la connectivité réseau
   - Vérifier les clés API

2. **Aucun résultat:**
   - Vérifier la configuration du moteur de recherche
   - Tester avec des requêtes simples
   - Vérifier les sources configurées

3. **Erreurs de performance:**
   - Réduire le nombre de résultats
   - Optimiser les requêtes
   - Vérifier les timeouts

### Contact

Pour toute question ou problème:
- Vérifier les logs de l'application
- Consulter la documentation Google Custom Search API
- Tester avec l'interface web de debug

## Roadmap

### Améliorations futures

1. **Cache avancé:**
   - Cache Redis pour les résultats
   - Expiration intelligente

2. **Analytics:**
   - Métriques d'utilisation
   - Analyse des performances

3. **Intégration étendue:**
   - Plus de sources financières
   - Types de recherche supplémentaires

4. **IA avancée:**
   - Analyse de sentiment plus sophistiquée
   - Extraction automatique d'entités

---

*Dernière mise à jour: $(date)* 