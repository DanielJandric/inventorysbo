# Update Marchés - Briefings Automatiques

## Vue d'ensemble

La fonctionnalité "Update Marchés" génère automatiquement des briefings narratifs sur les marchés financiers du jour, utilisant GPT-4o pour analyser les données de marché et créer un récit structuré.

## Fonctionnalités

### 🕐 Scheduler Automatique
- **Génération automatique** : Chaque jour à 21h30 CEST
- **Format narratif** : Briefing fluide et structuré comme un stratégiste
- **Sauvegarde** : Stockage automatique en base de données
- **Notifications** : Envoi automatique par email aux destinataires configurés

### 🎯 Déclenchement Manuel
- **Bouton "Générer Update"** : Déclenchement immédiat
- **Données actuelles** : Utilise les données de marché en temps réel
- **Flexibilité** : Permet de générer des briefings à la demande
- **Notifications** : Envoi automatique par email aux destinataires configurés

### 📊 Structure du Briefing
Le briefing suit un format narratif intégré :

1. **Actions** : USA, Europe, Suisse, autres zones si mouvement marquant
2. **Obligations souveraines** : US 10Y, Bund, OAT, BTP, Confédération
3. **Cryptoactifs** : BTC, ETH, capitalisation globale, régulation, flux
4. **Macro & Géopolitique** : Stats, décisions banques centrales, tensions
5. **Synthèse** : Ce qu'il faut retenir en une phrase + signaux à surveiller

## Installation

### 1. Créer la table Supabase
```bash
python create_market_updates_table.py
```

### 2. Vérifier les dépendances
La dépendance `schedule==1.2.0` est déjà incluse dans `requirements.txt`.

### 3. Configuration
Assurez-vous que les variables d'environnement suivantes sont configurées :
- `OPENAI_API_KEY` : Clé API OpenAI pour GPT-4o
- `SUPABASE_URL` et `SUPABASE_KEY` : Configuration Supabase
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENTS` : Configuration email pour les notifications automatiques

## Utilisation

### Interface Web
1. Accédez à `/markets` dans l'application
2. Consultez le statut du scheduler
3. Utilisez le bouton "Générer Update" pour un déclenchement manuel
4. Consultez l'historique des briefings générés

### API Endpoints

#### Récupérer les briefings
```http
GET /api/market-updates
```

#### Déclencher manuellement
```http
POST /api/market-updates/trigger
```

#### Statut du scheduler
```http
GET /api/market-updates/scheduler-status
```

## Configuration Avancée

### Modifier l'heure de génération
Dans `app.py`, modifiez la variable :
```python
MARKET_UPDATE_TIME = "21:30"  # Format HH:MM
```

### Personnaliser le prompt
Modifiez la fonction `generate_market_briefing()` dans `app.py` pour ajuster le style ou le contenu des briefings.

## Structure de la Base de Données

### Table `market_updates`
```sql
CREATE TABLE market_updates (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,           -- Contenu du briefing
    date VARCHAR(10) NOT NULL,       -- Date (YYYY-MM-DD)
    time VARCHAR(5) NOT NULL,        -- Heure (HH:MM)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trigger_type VARCHAR(20) DEFAULT 'manual',  -- 'manual' ou 'scheduled'
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Logs et Monitoring

Les logs incluent :
- ✅ Démarrage du scheduler
- 🔄 Génération de briefings
- 📧 Envoi de notifications par email
- ❌ Erreurs de génération

## Format des Emails

Les briefings sont envoyés par email avec :
- **Sujet** : "📊 Briefing de Marché - DD/MM/YYYY" (automatique) ou "(Manuel)"
- **Format HTML** : Mise en forme professionnelle avec couleurs BONVIN
- **Contenu** : Briefing complet avec métadonnées de génération
- **Destinataires** : Tous les emails configurés dans `EMAIL_RECIPIENTS`

## Dépannage

### Le scheduler ne démarre pas
- Vérifiez que la dépendance `schedule` est installée
- Consultez les logs pour les erreurs de configuration

### Erreur de génération
- Vérifiez la configuration OpenAI
- Consultez les logs pour les détails d'erreur

### Problèmes de base de données
- Vérifiez la connexion Supabase
- Assurez-vous que la table `market_updates` existe

## Intégration

La fonctionnalité s'intègre parfaitement avec :
- **Système de notifications Gmail** existant
- **Interface glasmorphique** cohérente
- **Menu de navigation** unifié
- **Système de cache** intelligent 