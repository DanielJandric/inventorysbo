# 🚀 Test de Charge GPT-5 Responses API

Ce script permet de tester les performances et la fiabilité de GPT-5 Responses API avec différents paramètres.

## 📋 Prérequis

```bash
# Installer les dépendances
pip install openai

# Configurer votre clé API
export OPENAI_API_KEY="sk-..."
```

## 🎯 Utilisation

### **Test basique (20 requêtes, 5 concurrentes)**
```bash
python load_test_gpt5.py
```

### **Test personnalisé**
```bash
# 50 requêtes, 10 concurrentes, timeout 30s, effort élevé
export LT_REQS=50
export LT_CONC=10
export LT_TIMEOUT=30
export LT_EFFORT=high
python load_test_gpt5.py
```

### **Test rapide (5 requêtes, 2 concurrentes)**
```bash
export LT_REQS=5
export LT_CONC=2
python load_test_gpt5.py
```

## ⚙️ Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `LT_REQS` | 20 | Nombre total de requêtes |
| `LT_CONC` | 5 | Nombre de requêtes concurrentes |
| `LT_TIMEOUT` | 60 | Timeout par requête (secondes) |
| `LT_MAXTOK` | 800 | Tokens de sortie maximum |
| `LT_EFFORT` | medium | Effort reasoning (low/medium/high) |

## 📊 Interprétation des résultats

### **Métriques affichées :**
- **Total** : Nombre total de requêtes
- **OK** : Requêtes réussies avec réponse
- **KO** : Requêtes en erreur
- **Empty text** : Réponses vides (problème GPT-5)

### **Latence :**
- **min/mean/p50/p95/max** : Statistiques de latence en millisecondes
- **p95** : 95% des requêtes sont plus rapides que cette valeur

### **Exemples de sortie :**
```
=== SUMMARY ===
Total: 20 | OK: 15 | KO: 5 | Empty text: 3
Latency ms -> min:1200.0 mean:3500.0 p50:3200.0 p95:8500.0 max:12000.0

Errors (up to 5):
- #3 8500.0ms :: TimeoutError: Request timed out
- #7 12000.0ms :: TimeoutError: Request timed out

Samples (up to 5):
- #1 1200.0ms [45 chars]: Les marchés suisses offrent des opportunités intéressantes.
- #2 1800.0ms [52 chars]: La volatilité actuelle reste modérée sur les indices.
```

## 🔍 Diagnostic des problèmes

### **Réponses vides (Empty text)**
- **Symptôme** : `Empty text: > 0`
- **Cause** : GPT-5 Responses API ne génère pas de contenu utilisable
- **Solution** : Ajuster les paramètres ou utiliser Chat Completions

### **Timeouts fréquents**
- **Symptôme** : Latence p95 très élevée
- **Cause** : Modèle trop lent ou paramètres trop exigeants
- **Solution** : Réduire `LT_EFFORT` ou `LT_MAXTOK`

### **Erreurs de rate limiting**
- **Symptôme** : Erreurs 429
- **Cause** : Trop de requêtes simultanées
- **Solution** : Réduire `LT_CONC`

## 🧪 Tests recommandés

### **Test de stabilité**
```bash
export LT_REQS=100
export LT_CONC=3
export LT_EFFORT=low
python load_test_gpt5.py
```

### **Test de performance**
```bash
export LT_REQS=50
export LT_CONC=10
export LT_EFFORT=high
python load_test_gpt5.py
```

### **Test de fiabilité**
```bash
export LT_REQS=200
export LT_CONC=5
export LT_TIMEOUT=30
python load_test_gpt5.py
```

## 🚨 Dépannage

### **Erreur "ModuleNotFoundError: No module named 'openai'"**
```bash
pip install --upgrade openai
```

### **Erreur "Invalid API key"**
```bash
export OPENAI_API_KEY="sk-..."
echo $OPENAI_API_KEY  # Vérifier que c'est bien défini
```

### **Erreur "Rate limit exceeded"**
- Réduire `LT_CONC`
- Augmenter l'intervalle entre les tests
- Vérifier votre quota OpenAI

## 📈 Analyse des résultats

### **Performance acceptable :**
- Latence moyenne < 5000ms
- Taux de succès > 90%
- Pas de réponses vides

### **Performance dégradée :**
- Latence moyenne > 10000ms
- Taux de succès < 80%
- Réponses vides fréquentes

### **Problèmes critiques :**
- Taux de succès < 50%
- Timeouts systématiques
- Réponses vides > 50%
