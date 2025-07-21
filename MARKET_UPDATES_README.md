# Update Marchés - Briefings Automatiques

## Vue d'ensemble

La fonctionnalité "Update Marchés" génère automatiquement des briefings narratifs sur les marchés financiers du jour, utilisant Gemini 1.5 Flash avec recherche web pour analyser les données de marché et créer un récit structuré.

## Fonctionnalités

### 🕐 Scheduler Automatique
- **Génération automatique** : Chaque jour à 21h30 CEST
- **Format narratif** : Briefing fluide et structuré comme un stratégiste
- **Sauvegarde** : Stockage automatique en base de données
- **Notifications** : Envoi automatique par email aux destinataires configurés

### 🎯 Déclenchement Manuel
- **Bouton "Générer Update"** : Déclenchement immédiat
- **Données actuelles** : Utilise les données de marché en temps réel via Google Search
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
- `GEMINI_API_KEY` : Clé API Google Gemini (recommandé)
- `OPENAI_API_KEY` : Clé API OpenAI (fallback si Gemini non configuré)
- `SUPABASE_URL` et `SUPABASE_KEY` : Configuration Supabase
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENTS` : Configuration email pour les notifications automatiques

## Utilisation

### Génération Automatique
- **Horaire** : 21h30 CEST quotidiennement
- **Sauvegarde** : Stockage en base de données
- **Notifications** : Email automatique aux destinataires

### Génération Manuelle
- **Interface** : Page `/markets`
- **Bouton** : "Générer Update"
- **Temps réel** : Données actuelles via Google Search

## API Endpoints

### Récupérer les briefings
```bash
GET /api/market-updates
```

### Déclencher une génération
```bash
POST /api/market-updates/trigger
```

### Statut du scheduler
```bash
GET /api/market-updates/scheduler-status
```

## Configuration Avancée

### Modifier l'horaire automatique
Dans `app.py`, ligne 4637 :
```python
MARKET_UPDATE_TIME = "21:30"  # Heure de génération automatique
```

### Modifier le timezone
```python
MARKET_UPDATE_TIMEZONE = "Europe/Paris"  # Timezone pour les updates
```

## Dépannage

### Erreur "GEMINI_API_KEY non configurée"
- Ajoutez votre clé Gemini dans le fichier `.env`
- Ou configurez-la dans les variables d'environnement Render

### Erreur "Quota exceeded"
- Les clés Gemini gratuites ont des limites
- L'application utilise automatiquement OpenAI comme fallback

### Erreur de connectivité
- Vérifiez votre connexion internet
- Vérifiez que la clé API est valide

## Logs

Les logs de génération sont disponibles dans les logs de l'application :
```python
logger.info("✅ Briefing généré avec Gemini 1.5 Flash + Google Search")
logger.error(f"Erreur API Gemini: {response.status_code} - {response.text}")
```

## Avantages de Gemini

### ✅ Recherche Web Intégrée
- Données en temps réel via Google Search
- Pas besoin de configurer des APIs boursières séparées
- Actualités macro et géopolitiques incluses

### ✅ Performance
- Modèle Gemini 1.5 Flash optimisé
- Réponse rapide (< 10 secondes)
- Gestion automatique des erreurs

### ✅ Coût
- Clés gratuites disponibles
- Limites généreuses pour usage personnel
- Pas de coût par requête (dans les limites) 