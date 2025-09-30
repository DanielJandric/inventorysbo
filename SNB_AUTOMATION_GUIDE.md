# 🤖 GUIDE D'AUTOMATISATION SNB TAUX

Ce guide explique comment mettre en place la collecte **100% automatique** des données SNB.

---

## 📋 ARCHITECTURE AUTOMATIQUE

```
┌─────────────────────────────────────────────────────────┐
│                    RENDER CRON JOBS                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │   QUOTIDIEN      │    │    MENSUEL       │          │
│  │   18h00 UTC      │    │  5 du mois 9h    │          │
│  │  (OIS approx.)   │    │  (CPI + KOF)     │          │
│  └────────┬─────────┘    └────────┬─────────┘          │
│           │                       │                     │
│           └───────────┬───────────┘                     │
│                       ▼                                 │
│            ┌──────────────────────┐                     │
│            │ snb_auto_scraper.py  │                     │
│            │  + ScrapingBee API   │                     │
│            └──────────┬───────────┘                     │
│                       │                                 │
└───────────────────────┼─────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Supabase DB    │
              │  (tables SNB)   │
              └─────────┬───────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Modèle BNS     │
              │  (calcul auto)  │
              └─────────────────┘
```

---

## 🚀 INSTALLATION (5 ÉTAPES)

### **ÉTAPE 1 : Créer un compte ScrapingBee**

1. Allez sur https://www.scrapingbee.com/
2. Créez un compte (1000 crédits gratuits)
3. Récupérez votre **API Key** depuis le dashboard

---

### **ÉTAPE 2 : Configurer les variables d'environnement**

#### **A) Dans votre fichier local `.env` :**

```bash
# Ajouter dans .env
SCRAPINGBEE_API_KEY=votre_clé_scrapingbee_ici
SNB_API_BASE_URL=https://inventorysbo.onrender.com
SNB_NOTIFICATION_EMAIL=votre-email@exemple.com  # Optionnel
```

#### **B) Dans Render Dashboard :**

1. Allez sur https://dashboard.render.com
2. Sélectionnez votre service `inventorysbo`
3. Cliquez sur **"Environment"**
4. Ajoutez :
   - `SCRAPINGBEE_API_KEY` = `votre_clé`
   - `SNB_API_BASE_URL` = `https://inventorysbo.onrender.com`

---

### **ÉTAPE 3 : Déployer les fichiers**

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">git add snb_auto_scraper.py render_cron.yaml SNB_AUTOMATION_GUIDE.md
