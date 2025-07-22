# 🔧 Configuration des Clés API sur Render

## 🚨 **PROBLÈME ACTUEL**
Les erreurs `401 Unauthorized` indiquent que les clés API ne sont pas configurées sur Render.

## ✅ **SOLUTION**

### 1. **Aller sur le Dashboard Render**
- Ouvrir https://dashboard.render.com
- Se connecter à votre compte

### 2. **Sélectionner le Service**
- Cliquer sur votre service `inventorysbo`
- Aller dans l'onglet **Environment**

### 3. **Ajouter les Variables d'Environnement**

Ajouter ces 3 variables :

```
ALPHA_VANTAGE_KEY=XCRQGI1OMS5381DE
EODHD_KEY=687ae6e8493e52.65071366
FINNHUB_KEY=d1tbknpr01qr2iithm20d1tbknpr01qr2iithm2g
```

### 4. **Redéployer le Service**
- Cliquer sur **Manual Deploy**
- Sélectionner **Deploy latest commit**

## 🧪 **TEST DES CLÉS**

Les clés ont été testées localement :
- ✅ **EODHD** : Fonctionnel (AAPL = $213.40)
- ✅ **Finnhub** : Fonctionnel (AAPL = $213.50)
- ⚠️ **Alpha Vantage** : Limite quotidienne atteinte (25 req/jour)

## 🔄 **SYSTÈME DE FALLBACK**

Le nouveau système utilise l'ordre :
1. **Alpha Vantage** (si disponible)
2. **EODHD** (principal)
3. **Finnhub** (backup)

## 📊 **RÉSULTAT ATTENDU**

Après configuration, vous devriez voir :
```
✅ EODHD: Fonctionnel pour TSLA
✅ Finnhub: Fonctionnel pour TSLA
```

Au lieu de :
```
❌ Erreur EODHD: 401 Unauthorized
❌ Erreur Finnhub: 401 Unauthorized
``` 