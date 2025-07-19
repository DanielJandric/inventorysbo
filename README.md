# 🚀 BONVIN - Collection Privée

Application de gestion d'inventaire sophistiquée avec **IA avancée**, **recherche sémantique RAG**, **gestion d'actions boursières** et **génération de PDFs professionnels**.

## 📊 Statistiques du Projet
- **11,695 lignes de code** au total
- **5,197 lignes Python** (45%)
- **34 fichiers** de code
- **Application de taille moyenne à grande**

## 🎯 Fonctionnalités Principales

### 🎨 Interface Utilisateur Glassmorphique
- **Design moderne** avec effets de transparence et animations fluides
- **Logo BONVIN** avec effet de brillance intégré
- **Responsive design** optimisé pour tous les appareils
- **Mode sombre** avec dégradés dynamiques
- **Lazy loading** des cartes pour performance optimale

### 📈 Dashboard Statistiques Avancées
- **Total des objets** avec animations temps réel
- **Objets vendus vs disponibles** avec compteurs dynamiques
- **Valeur totale** en CHF avec calculs automatiques
- **Âge moyen** de la collection
- **Taux de conversion** et métriques de performance
- **Statistiques par catégorie** détaillées

### 🔍 Système de Filtres Multi-critères
- **Filtres par catégorie** : Voitures, Bateaux, Immobilier, Be Capital, Start-ups, Avions, Montres, Art, Bijoux, Vins
- **Filtres par statut** : Disponible, Vendu, En vente
- **Recherche textuelle avancée** avec recherche sémantique
- **Modes d'affichage** : Cartes animées ou Liste compacte
- **Compteurs dynamiques** pour chaque filtre

### 🤖 IA Avancée avec RAG (Retrieval-Augmented Generation)
- **Assistant BONVIN** avec GPT-4 et recherche sémantique
- **Recherche intelligente** dans la collection avec variations de termes
- **Embeddings automatiques** pour chaque objet
- **Cache multi-niveaux** pour optimiser les performances
- **Analyse de performance** automatisée
- **Questions contextuelles** avec suggestions intelligentes

#### Exemples de questions IA :
- **"Combien de Ferrari ?"** → Recherche et compte automatique
- **"Où j'en suis avec mes ventes ?"** → Analyse de performance complète
- **"Comment va ma collection ?"** → Vue d'ensemble patrimoniale
- **"Que dois-je vendre ?"** → Conseils stratégiques IA
- **"Statistiques complètes"** → Dashboard détaillé

### 📈 Gestion d'Actions Boursières
- **Actions cotées** avec symboles boursiers
- **Prix temps réel** via API Yahoo Finance
- **Quantités et valeurs** calculées automatiquement
- **Prix d'acquisition** et prix actuels
- **Gestion des portefeuilles** d'actions
- **Calculs de plus-values** automatiques

### 💰 Estimation IA de Prix
- **OpenAI GPT-4** pour estimations de marché précises
- **Analyse contextuelle** basée sur nom, catégorie, année
- **Estimation en CHF** adaptée au marché suisse
- **Niveau de confiance** avec scoring 0.1-0.9
- **Analyse détaillée** et raisonnement explicite
- **Modal d'estimation** avec design professionnel

### 📄 Génération de PDFs Professionnels
- **Rapports PDF** optimisés noir et blanc
- **Styles professionnels** avec en-têtes et pieds de page
- **Gestion mémoire** optimisée pour éviter les erreurs SIGKILL
- **Module d'optimisation** dédié (`pdf_optimizer.py`)
- **Templates HTML** spécialisés pour PDFs
- **Formats multiples** : Portefeuille, par catégorie, complet

### 📧 Notifications Email
- **Système de notifications** Gmail intégré
- **Destinataires multiples** configurables
- **Notifications automatiques** pour événements importants
- **Templates email** professionnels

### 📝 CRUD Complet avec Validation
- **Créer** de nouveaux objets avec formulaire intelligent
- **Modifier** les objets existants en un clic
- **Supprimer** avec confirmation de sécurité
- **Gestion des statuts** : Disponible/Vendu
- **Gestion du flag "En vente"** pour objets disponibles
- **Champs spécialisés** : Surface, revenus locatifs, actions boursières
- **Validation** côté client et serveur

## 🛠 Stack Technologique

### Backend
- **Flask 3.0.3** - Framework web Python moderne
- **Flask-CORS 4.0.0** - Gestion CORS pour API
- **Gunicorn 21.2.0** - Serveur WSGI de production
- **Python 3.11+** - Version optimisée
- **WeasyPrint** - Génération PDF professionnelle

### Frontend
- **HTML5** sémantique avec templates Jinja2
- **Tailwind CSS** - Framework CSS utilitaire via CDN
- **JavaScript Vanilla ES6+** - Interactions dynamiques
- **Intersection Observer API** - Lazy loading des cartes
- **CSS Custom Properties** - Variables CSS avancées

### Base de Données
- **Supabase** - PostgreSQL cloud avec API REST
- **API REST** pour toutes les opérations CRUD
- **Gestion des relations** et contraintes
- **Index optimisés** pour les performances

### Intelligence Artificielle
- **OpenAI GPT-4** - Modèle avancé pour chat et estimation
- **OpenAI Embeddings** - text-embedding-3-small pour recherche sémantique
- **Prompt engineering** spécialisé pour évaluation d'objets
- **Recherche sémantique** avec variations de termes
- **Cache intelligent** pour optimiser les coûts API

### Services Externes
- **Yahoo Finance API** - Prix temps réel des actions
- **Gmail API** - Notifications email
- **Render** - Déploiement cloud

## 🏗 Installation et Configuration

### Prérequis
- **Python 3.11+**
- **Compte Supabase** (gratuit)
- **Clé API OpenAI** (GPT-4)
- **Compte Gmail** (pour notifications)

### Installation Locale

1. **Cloner le repository**
```bash
git clone https://github.com/DanielJandric/inventorysbo.git
cd inventorysbo
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration des variables d'environnement**
Créer un fichier `.env` :
```env
# Configuration Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_clé_supabase_anon

# Configuration OpenAI
OPENAI_API_KEY=votre_clé_openai_gpt4

# Configuration Gmail (optionnel)
GMAIL_USER=votre_email@gmail.com
GMAIL_PASSWORD=votre_mot_de_passe_app
GMAIL_RECIPIENTS=email1@example.com,email2@example.com
```

5. **Migration de la base de données**
Exécuter dans Supabase SQL Editor :
```sql
-- Table principale
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    construction_year INTEGER,
    condition VARCHAR(50),
    surface_m2 DECIMAL(10,2),
    rental_income_chf DECIMAL(15,2),
    acquisition_price DECIMAL(15,2),
    asking_price DECIMAL(15,2),
    sold_price DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'Available',
    for_sale BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table pour les actions boursières
CREATE TABLE stock_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    stock_symbol VARCHAR(20),
    stock_quantity INTEGER,
    stock_purchase_price DECIMAL(15,2),
    current_price DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index pour les performances
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_for_sale ON items(for_sale);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_stock_symbol ON stock_items(stock_symbol);
```

6. **Lancer l'application**
```bash
python app.py
```

Application accessible sur `http://localhost:5000`

## 🗄 Structure de la Base de Données

### Table `items` - Objets de Collection
```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,                    -- ID unique auto-incrémenté
    name VARCHAR(255) NOT NULL,               -- Nom de l'objet (requis)
    category VARCHAR(100),                    -- Catégorie (Voitures, Montres, etc.)
    construction_year INTEGER,                -- Année de construction/fabrication
    condition VARCHAR(50),                    -- État (Neuf, Excellent, etc.)
    surface_m2 DECIMAL(10,2),                -- Surface en m² (immobilier)
    rental_income_chf DECIMAL(15,2),         -- Revenus locatifs CHF/mois
    acquisition_price DECIMAL(15,2),         -- Prix d'acquisition
    asking_price DECIMAL(15,2),              -- Prix demandé
    sold_price DECIMAL(15,2),                -- Prix de vente final
    status VARCHAR(20) DEFAULT 'Available',  -- Statut : Available/Sold
    for_sale BOOLEAN DEFAULT FALSE,          -- En vente (objets disponibles)
    description TEXT,                        -- Description détaillée
    created_at TIMESTAMP DEFAULT NOW(),      -- Date de création
    updated_at TIMESTAMP DEFAULT NOW()       -- Dernière modification
);
```

### Table `stock_items` - Actions Boursières
```sql
CREATE TABLE stock_items (
    id SERIAL PRIMARY KEY,                    -- ID unique auto-incrémenté
    name VARCHAR(255) NOT NULL,               -- Nom de l'action
    stock_symbol VARCHAR(20),                 -- Symbole boursier (ex: AAPL)
    stock_quantity INTEGER,                   -- Quantité d'actions
    stock_purchase_price DECIMAL(15,2),      -- Prix d'acquisition par action
    current_price DECIMAL(15,2),             -- Prix actuel (mis à jour automatiquement)
    status VARCHAR(20) DEFAULT 'Available',  -- Statut : Available/Sold
    created_at TIMESTAMP DEFAULT NOW(),      -- Date de création
    updated_at TIMESTAMP DEFAULT NOW()       -- Dernière modification
);
```

## 🔌 API Endpoints

### Objets de Collection (CRUD)
- `GET /api/items` - Récupérer tous les objets avec tri par date
- `POST /api/items` - Créer un nouvel objet
- `PUT /api/items/{id}` - Mettre à jour un objet existant
- `DELETE /api/items/{id}` - Supprimer un objet (avec confirmation)

### Actions Boursières
- `GET /api/stocks` - Récupérer toutes les actions
- `POST /api/stocks` - Créer une nouvelle action
- `PUT /api/stocks/{id}` - Mettre à jour une action
- `DELETE /api/stocks/{id}` - Supprimer une action

### Intelligence Artificielle
- `GET /api/market-price/{id}` - Estimation de prix IA pour un objet
- `POST /api/chatbot` - Chat avec l'assistant IA BONVIN
- `POST /api/generate-embeddings` - Génération d'embeddings pour recherche sémantique

### Génération de PDFs
- `GET /api/portfolio/pdf` - Rapport PDF du portefeuille complet
- `GET /api/reports/asset-class/{asset_class_name}` - Rapport PDF par catégorie
- `GET /api/reports/all-asset-classes` - Rapport PDF de toutes les catégories

### Monitoring
- `GET /health` - Status de santé de l'application
- `GET /api/test` - Test des connexions API (Supabase + OpenAI)

## 🚀 Déploiement

### Version de Production
**Application déployée :** https://inventorysbo.onrender.com

### Caractéristiques de Production
- ✅ **Application complète** avec toutes les fonctionnalités
- ✅ **IA avancée** avec RAG et recherche sémantique
- ✅ **Gestion d'actions** avec prix temps réel
- ✅ **Génération PDFs** optimisée et professionnelle
- ✅ **Notifications email** automatiques
- ✅ **Interface responsive** multi-device
- ✅ **Performance optimisée** avec cache et lazy loading

### Déploiement Render

1. **Configurer render.yaml**
```yaml
services:
  - type: web
    name: inventorysbo
    env: python
    plan: starter
    buildCommand: "./build.sh"
    startCommand: "./start.sh"
    healthCheckPath: /health
```

2. **Variables d'environnement Render**
- `SUPABASE_URL` : URL de votre projet Supabase
- `SUPABASE_KEY` : Clé anonyme Supabase
- `OPENAI_API_KEY` : Clé API OpenAI
- `GMAIL_USER` : Email Gmail pour notifications
- `GMAIL_PASSWORD` : Mot de passe d'application Gmail
- `GMAIL_RECIPIENTS` : Destinataires séparés par virgules

## 📊 Fonctionnalités Avancées

### 🔍 Recherche Sémantique RAG
- **Embeddings automatiques** pour chaque objet
- **Recherche par similarité** cosinus
- **Cache intelligent** pour optimiser les performances
- **Détection d'intention** de requête
- **Suggestions contextuelles** basées sur l'historique

### 📈 Gestion Financière
- **Calculs automatiques** de valeurs totales
- **Suivi des plus-values** pour actions
- **Analyse de performance** par catégorie
- **Estimation de marché** par IA
- **Rapports financiers** PDF

### 🎨 Personnalisation PDFs
- **Styles professionnels** noir et blanc
- **En-têtes et pieds de page** automatiques
- **Gestion des sauts de page** intelligente
- **Optimisation mémoire** pour éviter les erreurs
- **Templates personnalisables** par type de rapport

## 💻 Développement

### Structure du Projet
```
inventorysbo/
├── app.py                 # Application principale Flask
├── pdf_optimizer.py       # Module d'optimisation PDF
├── requirements.txt       # Dépendances Python
├── templates/            # Templates HTML
│   ├── index.html        # Interface principale
│   └── pdf_portfolio_optimized.html  # Template PDF
├── static/               # Assets statiques
│   ├── script.js         # JavaScript principal
│   └── *.png            # Images et logos
├── build.sh             # Script de build Render
├── start.sh             # Script de démarrage
└── render.yaml          # Configuration Render
```

### Scripts Utiles
- `python app.py` - Lancer en développement
- `pip install -r requirements.txt` - Installer dépendances
- `git add . && git commit -m "message"` - Commiter les changements

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commiter les changements (`git commit -m 'Add AmazingFeature'`)
4. Pousser vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou support :
- **Email** : daniel.jandric@investis.ch
- **GitHub Issues** : [Créer une issue](https://github.com/DanielJandric/inventorysbo/issues)

---

**BONVIN Collection** - Gestion d'inventaire intelligente avec IA 🚀
