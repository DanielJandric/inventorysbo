# Migration vers Yahoo Finance API

## 🎯 **Objectif**

Remplacer l'ancienne logique de prix d'actions basée sur ChatGPT par une solution robuste utilisant Yahoo Finance API avec gestion intelligente des limites et stockage local des prix historiques.

## 🔄 **Changements Principaux**

### 1. **Nouveau Gestionnaire de Prix**
- **Fichier**: `stock_price_manager.py`
- **Fonctionnalités**:
  - Récupération de prix via Yahoo Finance API
  - Cache intelligent (1 heure)
  - Stockage local des prix historiques (30 jours)
  - Limite de 5 requêtes par jour
  - Gestion automatique des symboles par bourse

### 2. **Stockage Local des Données**
- **Répertoire**: `stock_data/`
- **Fichiers**:
  - `price_cache.json` : Cache des prix actuels
  - `price_history.json` : Historique des prix (30 jours)
  - `daily_requests.json` : Compteur de requêtes quotidiennes

### 3. **Nouvelles Routes API**

#### Récupération de prix
```
GET /api/stock-price/<symbol>
```
- Utilise Yahoo Finance API
- Cache intelligent
- Gestion des limites quotidiennes

#### Historique des prix
```
GET /api/stock-price/history/<symbol>?days=30
```
- Récupère l'historique local
- Paramètre `days` optionnel (défaut: 30)

#### Statut du cache
```
GET /api/stock-price/cache/status
```
- Informations sur le cache
- Compteur de requêtes quotidiennes
- Statut des limites

#### Statut Yahoo Finance
```
GET /api/yahoo-finance/status
```
- Test de connectivité
- Validation de l'API

### 4. **Gestion des Symboles**

#### Actions Suisses
- **Format**: `SYMBOL.SW`
- **Exemples**: `NOVN.SW`, `ROG.SW`, `NESN.SW`

#### Actions Américaines
- **Format**: `SYMBOL`
- **Exemples**: `AAPL`, `MSFT`, `GOOGL`

#### Actions Européennes
- **Format**: `SYMBOL.L` (Londres)
- **Exemples**: `HSBA.L`, `VOD.L`

## 📊 **Avantages de la Nouvelle Solution**

### ✅ **Fiabilité**
- Données réelles de Yahoo Finance
- Pas de dépendance à ChatGPT pour les prix
- Validation des données

### ✅ **Performance**
- Cache intelligent (1 heure)
- Stockage local des historiques
- Réduction des appels API

### ✅ **Contrôle des Coûts**
- Limite de 5 requêtes par jour
- Gestion automatique des quotas
- Fallback vers le cache

### ✅ **Données Riches**
- Prix actuels et historiques
- Métriques boursières complètes
- Volume, PE ratio, dividendes
- High/Low 52 semaines

## 🔧 **Configuration**

### Variables d'Environnement
Aucune nouvelle variable requise. Yahoo Finance API est gratuite et ne nécessite pas de clé.

### Dépendances
```bash
pip install yfinance pandas
```

## 📈 **Utilisation**

### Mise à Jour Manuelle
```javascript
// Récupérer un prix
fetch('/api/stock-price/AAPL')
  .then(response => response.json())
  .then(data => console.log(data));

// Forcer le refresh
fetch('/api/stock-price/AAPL?force_refresh=true')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Mise à Jour Automatique
- **Fréquence**: 5 fois par jour
- **Heures**: 09:00, 11:00, 13:00, 15:00, 17:00, 21:30
- **Limite**: Maximum 5 requêtes par jour

### Historique des Prix
```javascript
// Récupérer l'historique
fetch('/api/stock-price/history/AAPL?days=7')
  .then(response => response.json())
  .then(data => console.log(data.history));
```

## 🗂️ **Structure des Données**

### Prix Actuel
```json
{
  "symbol": "AAPL",
  "price": 211.18,
  "currency": "USD",
  "change": 0.31,
  "change_percent": 0.15,
  "volume": 48939500,
  "market_cap": 3312345678901,
  "pe_ratio": 28.5,
  "dividend_yield": 0.5,
  "high_52_week": 220.0,
  "low_52_week": 150.0,
  "timestamp": "2025-07-20T15:34:00",
  "source": "Yahoo Finance"
}
```

### Historique
```json
{
  "symbol": "AAPL",
  "history": [
    {
      "date": "2025-07-20",
      "time": "15:34",
      "price": 211.18,
      "change": 0.31,
      "change_percent": 0.15,
      "volume": 48939500
    }
  ],
  "days": 7,
  "source": "Yahoo Finance"
}
```

## 🔍 **Monitoring**

### Statut du Cache
```json
{
  "cache_size": 4,
  "history_size": 4,
  "daily_requests": 5,
  "max_daily_requests": 5,
  "last_request_date": "2025-07-20",
  "can_make_request": false,
  "cache_duration": 3600,
  "source": "Yahoo Finance",
  "api_limit_warning": "⚠️ Limite quotidienne: 5/5 requêtes"
}
```

## 🚀 **Migration Complète**

### Étapes Effectuées
1. ✅ Création du `StockPriceManager`
2. ✅ Remplacement des routes API
3. ✅ Mise à jour du scheduler automatique
4. ✅ Ajout des nouvelles routes d'historique
5. ✅ Tests de validation
6. ✅ Documentation

### Fichiers Modifiés
- `app.py` : Routes et logique principale
- `stock_price_manager.py` : Nouveau gestionnaire
- `requirements.txt` : Dépendances
- `test_yahoo_finance.py` : Tests

### Fichiers Créés
- `stock_data/` : Répertoire de stockage local
- `YAHOO_FINANCE_MIGRATION.md` : Cette documentation

## 🎉 **Résultat**

La logique des prix d'actions est maintenant :
- **Fiable** : Données réelles de Yahoo Finance
- **Efficace** : Cache intelligent et stockage local
- **Contrôlée** : Limite de 5 requêtes par jour
- **Complète** : Historique et métriques détaillées
- **Maintenable** : Code modulaire et documenté

## 🔮 **Prochaines Étapes**

1. **Déploiement** : Pousser les changements sur Render
2. **Monitoring** : Surveiller les performances
3. **Optimisation** : Ajuster les limites si nécessaire
4. **Extension** : Ajouter d'autres métriques si besoin 