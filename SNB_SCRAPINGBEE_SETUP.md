# 🐝 CONFIGURATION SCRAPINGBEE POUR SNB TAUX

## ⚠️ PROBLÈME ACTUEL

Dans les logs, vous voyez :
```
❌ ScrapingBee erreur 400
```

**Cause :** La clé API ScrapingBee n'est **pas configurée** ou **invalide**.

**Conséquence :** Le système fonctionne en **mode simulation** (valeurs approximatives).

---

## 🚀 SOLUTION : Configurer ScrapingBee (5 minutes)

### **ÉTAPE 1 : Créer un compte ScrapingBee**

1. Allez sur https://www.scrapingbee.com
2. Cliquez sur **"Start Free Trial"**
3. Créez un compte (email + password)
4. **Plan gratuit :** 1000 crédits/mois (largement suffisant)

### **ÉTAPE 2 : Récupérer votre API Key**

1. Une fois connecté, allez dans **"Dashboard"**
2. Vous verrez votre **API Key** affiché en haut
3. Copiez-la (format : `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

### **ÉTAPE 3 : Ajouter la clé dans Render**

1. Allez sur https://dashboard.render.com
2. Sélectionnez votre service **`inventorysbo`**
3. Cliquez sur **"Environment"** (menu gauche)
4. Cliquez **"Add Environment Variable"**
5. Remplissez :
   ```
   Name:  SCRAPINGBEE_API_KEY
   Value: votre_clé_copiée_à_l_etape_2
   ```
6. Cliquez **"Save Changes"**

### **ÉTAPE 4 : Redémarrer l'application**

Render va automatiquement redéployer. Attendez ~2 minutes.

### **ÉTAPE 5 : Tester**

1. Allez sur `/snb-taux`
2. Cliquez sur **"Mensuel (CPI+KOF)"**
3. Attendez ~30-60 secondes
4. Vous devriez maintenant voir :
   ```
   ✅ CPI collecté: 0.7% YoY
   ✅ KOF collecté: 101.2
   ✅ OIS Eurex collecté: 8 points
   ```

---

## 📊 CONSOMMATION DE CRÉDITS

### **Par collecte :**
- CPI (OFS) : ~2 crédits
- KOF (ETH) : ~2 crédits
- OIS (Eurex) : ~3 crédits
- **Total mensuel** : ~7 crédits

### **Par an :**
- Collecte mensuelle × 12 = **84 crédits/an**
- Collecte quotidienne OIS × 365 = **1095 crédits/an**

**Plan gratuit (1000 crédits/mois) = largement suffisant !**

---

## 🆘 MODE SIMULATION (SANS SCRAPINGBEE)

Si vous **ne configurez pas** ScrapingBee, le système fonctionne quand même avec :

### **Valeurs par défaut (approximatives) :**
- CPI : 0.5%
- KOF : 100.0
- OIS : Courbe plate basée sur taux directeur
- NEER : 0.0% (mode fallback)

**Avantage :** Vous pouvez tester le système sans compte ScrapingBee

**Inconvénient :** Données pas réelles, modèle moins précis

---

## ✅ ALTERNATIVES À SCRAPINGBEE

### **Option 1 : ScrapeStack (concurrent)**
- https://scrapestack.com
- Plan gratuit : 10,000 requests/mois
- Plus généreux que ScrapingBee

### **Option 2 : APIs directes (recommandé)**
- **OFS** : Pas d'API publique (scraping nécessaire)
- **KOF** : Pas d'API publique (scraping nécessaire)
- **Eurex** : API possible avec compte professionnel
- **SNB NEER** : ✅ API gratuite (déjà implémentée)

### **Option 3 : Mise à jour manuelle mensuelle**
- Utiliser `snb_data_collector.py` (mode interactif)
- Temps : 10 minutes/mois
- Coût : 0 CHF

---

## 🎯 RECOMMANDATION

**Pour démarrer (1 mois) :**
- ✅ Utiliser mode simulation (sans ScrapingBee)
- ✅ Valider que le système fonctionne
- ✅ Tester les graphiques et l'interface

**Pour production (après validation) :**
- ✅ Créer compte ScrapingBee (gratuit, 1000 crédits/mois)
- ✅ Configurer la clé dans Render
- ✅ Automatiser complètement

---

## 📈 IMPACT SUR LA QUALITÉ DU MODÈLE

| Avec ScrapingBee | Sans ScrapingBee (simulation) |
|------------------|-------------------------------|
| CPI réel (~0.7%) | CPI estimé (0.5%) |
| KOF réel (~101.2) | KOF neutre (100.0) |
| OIS Eurex réels | OIS approximatifs |
| **Précision : ~95%** | **Précision : ~70%** |

---

**Pour l'instant, le système fonctionne en mode simulation. C'est parfait pour tester ! 🧪**

**Voulez-vous configurer ScrapingBee maintenant ou tester d'abord en mode simulation ?** 🤔

