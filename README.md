# BONVIN - Collection Privée

Application de gestion d'inventaire sophistiquée avec interface glassmorphique, chatbot IA intelligent et estimation de prix automatisée.

## 🚀 Fonctionnalités

### 🎨 Interface Utilisateur
- **Design glassmorphique avancé** avec effets de transparence, flou et animations
- **Logo BONVIN intégré** avec effet de brillance
- **Responsive design** optimisé desktop, tablette et mobile
- **Animations fluides** et transitions élégantes avec lazy loading
- **Mode sombre** avec dégradés dynamiques

### 📊 Dashboard Statistiques Avancées
- **Total des objets** dans la collection avec animations
- **Objets vendus** vs **disponibles** avec compteurs temps réel
- **Valeur totale** des ventes et objets disponibles (CHF)
- **Âge moyen** de la collection calculé automatiquement
- **Taux de conversion** et métriques de performance

### 🔍 Système de Filtres Multi-critères
- **Filtres par catégorie** : Voitures, Bateaux, Appartements/Maison, Be Capital, Start-ups, Avions, Montres, Art, Bijoux, Vins
- **Filtres par statut** : Disponible, Vendu
- **Filtres par disponibilité** : En vente, Pas en vente (pour objets disponibles)
- **Recherche textuelle avancée** par nom, catégorie, description
- **Modes d'affichage** : Cartes avec animations ou Liste compacte
- **Compteurs dynamiques** pour chaque filtre

### 🔥 Gestion "En Vente" Intelligente
- **Flag "En vente"** pour objets disponibles uniquement
- **Indicateur visuel rouge** 🔥 pour identification rapide
- **Filtrage combiné** statut + disponibilité pour vente
- **Compteurs séparés** pour suivi détaillé des ventes
- **Cartes spéciales** avec design rouge discret pour objets en vente

### 🤖 Chatbot IA Intelligent
- **Assistant BONVIN** intégré avec GPT-4o-mini
- **Recherche sémantique** dans la collection avec variations de termes
- **Analyse de performance** automatisée
- **Statistiques en temps réel** via conversation
- **Questions rapides** prédéfinies pour navigation rapide
- **Suggestions contextuelles** basées sur les réponses
- **Gestion de l'historique** de conversation
- **Raccourcis clavier** : Ctrl/Cmd+K pour ouvrir, Échap pour fermer

#### Exemples de questions supportées :
- **"Combien de Ferrari ?"** → Recherche et compte automatique
- **"Où j'en suis avec mes ventes ?"** → Analyse de performance complète
- **"Comment va ma collection ?"** → Vue d'ensemble patrimoniale
- **"Que dois-je vendre ?"** → Conseils stratégiques
- **"Statistiques complètes"** → Dashboard détaillé

### 💰 Estimation IA de Prix
- **OpenAI GPT-4o-mini** pour estimations de marché
- **Analyse contextuelle** basée sur nom, catégorie, année
- **Estimation en CHF** adaptée au marché suisse
- **Niveau de confiance** avec scoring 0.1-0.9
- **Analyse détaillée** et raisonnement explicite
- **Modal d'estimation** avec design glassmorphique

### 📝 CRUD Complet avec Validation
- **Créer** de nouveaux objets avec formulaire intelligent
- **Modifier** les objets existants en un clic
- **Supprimer** avec confirmation de sécurité
- **Gestion des statuts** : Disponible/Vendu
- **Gestion du flag "En vente"** pour objets disponibles
- **Champs spécialisés** : Surface et revenus locatifs pour l'immobilier
- **Validation** côté client et serveur

## 🛠 Technologies

### Backend
- **Flask 3.0.3** - Framework web Python moderne
- **Flask-CORS 4.0.0** - Gestion CORS pour API
- **Gunicorn 21.2.0** - Serveur WSGI de production
- **Python 3.11+** - Version optimisée

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

### Intelligence Artificielle
- **OpenAI GPT-4o-mini** - Modèle optimisé pour chat et estimation
- **Prompt engineering** spécialisé pour évaluation d'objets
- **Recherche sémantique** avec variations de termes
- **Analyse contextuelle** des données de collection

## 🏗 Installation et Configuration

### Prérequis
- **Python 3.11+**
- **Compte Supabase** (gratuit)
- **Clé API OpenAI** (GPT-4o-mini)

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

-- Index pour les performances
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_for_sale ON items(for_sale);
CREATE INDEX idx_items_category ON items(category);
```

6. **Lancer l'application**
```bash
python app.py
```

Application accessible sur `http://localhost:5000`

## 🗄 Structure de la Base de Données

### Table `items` - Schéma Complet
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

### Logique Métier
- **Objet "Disponible"** : Peut être en collection privée (for_sale=false) ou en vente (for_sale=true)
- **Objet "En vente"** : Forcément "Disponible" avec for_sale=true
- **Objet "Vendu"** : Ne peut pas être "En vente", for_sale automatiquement false

## 🔌 API Endpoints

### Objets (CRUD)
- `GET /api/items` - Récupérer tous les objets avec tri par date
- `POST /api/items` - Créer un nouvel objet
- `PUT /api/items/{id}` - Mettre à jour un objet existant
- `DELETE /api/items/{id}` - Supprimer un objet (avec confirmation)

### Intelligence Artificielle
- `GET /api/market-price/{id}` - Estimation de prix IA pour un objet
- `POST /api/chatbot` - Chat avec l'assistant IA BONVIN

### Monitoring
- `GET /health` - Status de santé de l'application
- `GET /api/test` - Test des connexions API (Supabase + OpenAI)

## 🚀 Déploiement

### Version de Production
**Application déployée :** https://0vhlizck3nmg.manus.space/

### Caractéristiques de Production
- ✅ **205+ objets** chargés et optimisés
- ✅ **API OpenAI** opérationnelle avec gestion d'erreur robuste
- ✅ **Interface responsive** multi-device
- ✅ **Performance optimisée** avec mise en cache et lazy loading
- ✅ **Gestion "En vente"** complètement intégrée
- ✅ **Chatbot IA** intelligent avec recherche sémantique

### Déploiement Render

1. **Configurer render.yaml**
```yaml
services:
  - type: web
    name: bonvin-collection
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

3. **Scripts de build/start**
- `build.sh` : Installation des dépendances
- `start.sh` : Démarrage avec Gunicorn optimisé

## 💻 Développement

### Architecture du Projet
```
bonvin-collection/
├── app.py                     # Application Flask principale
├── requirements.txt           # Dépendances Python
├── build.sh                   # Script de build Render
├── start.sh                   # Script de démarrage
├── Procfile                   # Configuration Heroku
├── render.yaml                # Configuration Render
├── vercel.json                # Configuration Vercel
├── static/
│   ├── script.js              # JavaScript principal (2000+ lignes)
│   └── bonvin-logo.png        # Logo BONVIN officiel
├── templates/
│   └── index.html             # Template principal avec design glassmorphique
├── embed.py                   # Génération d'embeddings (futur)
├── regenerate_embeddings.py   # Régénération embeddings
└── README.md                  # Documentation complète
```

### Fonctionnalités Avancées du Code

#### JavaScript (script.js)
- **Glassmorphisme CSS** avec backdrop-filter avancé
- **Animations CSS** personnalisées avec IntersectionObserver
- **Gestion d'état** JavaScript sophistiquée multi-filtres
- **Lazy loading** des cartes avec animations d'apparition
- **Recherche intelligente** avec variations de termes
- **Validation** formulaires côté client
- **Chatbot intégré** avec suggestions contextuelles

#### Python (app.py)
- **API REST** complète avec gestion d'erreurs robuste
- **Chatbot IA** avec analyse sémantique avancée
- **Recherche multi-critères** sécurisée
- **Estimation de prix** via OpenAI GPT-4o-mini
- **Logging** détaillé pour debugging
- **Sécurité** avec validation des entrées

### Nouveautés Version 3.0
- ✅ **Chatbot IA intégré** avec GPT-4o-mini
- ✅ **Recherche sémantique** intelligente
- ✅ **Suggestions contextuelles** dans le chat
- ✅ **Raccourcis clavier** pour navigation rapide
- ✅ **Analyse de performance** automatisée
- ✅ **Interface glassmorphique** améliorée
- ✅ **Optimisations performance** et lazy loading

## 🔒 Sécurité

### Mesures Implémentées
- **Validation des entrées** côté client et serveur
- **Gestion d'erreurs** robuste pour éviter les crashes
- **Protection CORS** configurée
- **Sanitisation** des données utilisateur
- **Rate limiting** implicite via Render/Vercel
- **Variables d'environnement** sécurisées

## 📱 Responsive Design

### Breakpoints Supportés
- **Mobile** : 320px-768px (interface tactile optimisée)
- **Tablette** : 768px-1024px (cartes adaptatives)
- **Desktop** : 1024px+ (vue complète avec sidebar)
- **4K/Ultra-wide** : 1920px+ (grille étendue)

## 🎯 Performance

### Optimisations
- **Lazy loading** des cartes avec Intersection Observer
- **Debounce** sur la recherche pour éviter les requêtes excessives
- **Mise en cache** côté client des données statiques
- **Compression** Gzip sur Render/Vercel
- **CDN** Tailwind CSS pour chargement rapide
- **Animations CSS** hardware-accelerated

## 📞 Support et Contact

### Maintenance
- **Logs applicatifs** via `/health` endpoint
- **Monitoring** automatique Render/Vercel
- **Backup** automatique Supabase
- **Rollback** facile via Git

### Contact Technique
Pour questions, bugs ou nouvelles fonctionnalités :
- **GitHub Issues** : Rapports de bugs
- **Documentation** : README et commentaires code
- **API Testing** : Endpoint `/api/test` pour diagnostics

## 📄 Licence

**Propriétaire** - BONVIN Collection Privée  
Tous droits réservés. Usage interne uniquement.

---

**Version** : 3.0 - Chatbot IA Intelligent  
**Dernière mise à jour** : Janvier 2025  
**Compatibilité** : Python 3.11+, Navigateurs modernes  
**Status** : ✅ Production Ready
