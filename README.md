# BONVIN - Collection Privée

Application de gestion d'inventaire sophistiquée avec interface glassmorphique et estimation IA.

## Fonctionnalités

### 🎨 Interface Utilisateur
- **Design glassmorphique** avec effets de transparence et flou
- **Logo BONVIN animé** avec effet de brillance dorée
- **Responsive design** compatible desktop et mobile
- **Animations fluides** et transitions élégantes

### 📊 Dashboard Statistiques
- **Total des objets** dans la collection
- **Objets vendus** vs **disponibles**
- **Valeur totale** des ventes et objets disponibles
- **Âge moyen** de la collection

### 🔍 Filtres et Recherche
- **Filtres par catégorie** : Voitures, Bateaux, Immobilier, Be Capital, Start-ups, Avions, Montres, Art, Bijoux, Vins
- **Filtres par statut** : Disponible, Vendu
- **Recherche textuelle** par nom, catégorie, description
- **Modes d'affichage** : Cartes ou Liste

### 🤖 Estimation IA
- **OpenAI GPT-4o** pour estimations de prix
- **Analyse basée sur le titre** avec affinement par données complémentaires
- **Estimation en CHF** pour le marché suisse
- **Niveau de confiance** et analyse détaillée

### 📝 CRUD Complet
- **Créer** de nouveaux objets
- **Modifier** les objets existants
- **Supprimer** des objets
- **Gestion des statuts** (Disponible/Vendu)

## Technologies

### Backend
- **Flask** - Framework web Python
- **Flask-CORS** - Gestion des requêtes cross-origin
- **Requests** - Appels API HTTP

### Frontend
- **HTML5** avec templates Jinja2
- **Tailwind CSS** - Framework CSS utilitaire
- **JavaScript Vanilla** - Interactions dynamiques

### Base de Données
- **Supabase** - Base de données PostgreSQL cloud
- **API REST** pour toutes les opérations CRUD

### IA
- **OpenAI GPT-4o** - Estimation de prix intelligente
- **Prompt engineering** optimisé pour l'évaluation d'objets

## Installation

### Prérequis
- Python 3.11+
- Compte Supabase
- Clé API OpenAI

### Configuration

1. **Cloner le repository**
```bash
git clone https://github.com/DanielJandric/inventorysbo.git
cd inventorysbo
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration des variables d'environnement**
Créer un fichier `.env` basé sur `.env.example` :
```bash
cp .env.example .env
```

Puis modifier `.env` avec vos vraies clés :
```env
# Configuration Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_clé_supabase_anon

# Configuration OpenAI
OPENAI_API_KEY=votre_clé_openai
```

**Alternative :** Modifier directement dans `app.py` :
```python
# Configuration Supabase
SUPABASE_URL = "votre_url_supabase"
SUPABASE_KEY = "votre_clé_supabase"

# Configuration OpenAI
OPENAI_API_KEY = "votre_clé_openai"
```

4. **Lancer l'application**
```bash
python app.py
```

L'application sera accessible sur `http://localhost:5000`

## Structure de la Base de Données

### Table `items`
```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    construction_year INTEGER,
    condition VARCHAR(50),
    price DECIMAL(15,2),
    sold_price DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Objets
- `GET /api/items` - Récupérer tous les objets
- `POST /api/items` - Créer un nouvel objet
- `PUT /api/items/{id}` - Mettre à jour un objet
- `DELETE /api/items/{id}` - Supprimer un objet

### Estimation IA
- `GET /api/market-price/{id}` - Obtenir une estimation de prix

## Déploiement

### Version de Référence
L'application est déployée et fonctionnelle sur :
**https://0vhlizck3nmg.manus.space/**

### Caractéristiques de Production
- **205 objets** chargés depuis Supabase
- **API OpenAI** opérationnelle avec gestion d'erreur
- **Interface responsive** optimisée
- **Performances** optimisées avec mise en cache

## Développement

### Architecture
```
inventorysbo/
├── app.py              # Application Flask principale
├── requirements.txt    # Dépendances Python
├── static/            # Fichiers statiques
│   └── bonvin-logo.png # Logo BONVIN
└── README.md          # Documentation
```

### Fonctionnalités Avancées
- **Glassmorphisme** avec backdrop-filter CSS
- **Animations CSS** personnalisées
- **Gestion d'état** JavaScript sophistiquée
- **Validation** côté client et serveur
- **Gestion d'erreur** robuste

## Licence

Propriétaire - BONVIN Collection Privée

## Contact

Pour toute question ou support technique, contactez l'équipe de développement.

