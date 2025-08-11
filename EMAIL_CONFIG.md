# Configuration Email pour l'Envoi Automatique des Rapports

## Variables d'environnement à configurer dans Render

Pour que votre système envoie automatiquement les rapports d'analyse de marché par email, vous devez configurer ces variables dans votre dashboard Render :

### 1. Configuration SMTP

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=votre_email@gmail.com
EMAIL_PASSWORD=votre_mot_de_passe_app
```

### 2. Destinataires

```bash
EMAIL_RECIPIENTS=email1@example.com,email2@example.com,email3@example.com
```

## Configuration Gmail (Recommandé)

### 1. Activer l'authentification à 2 facteurs
- Allez dans les paramètres de votre compte Google
- Activez l'authentification à 2 facteurs

### 2. Générer un mot de passe d'application
- Allez dans "Sécurité" > "Connexion à Google"
- Cliquez sur "Mots de passe d'application"
- Générez un mot de passe pour "Mail"
- Utilisez ce mot de passe dans `EMAIL_PASSWORD`

### 3. Alternative : Compte de service
Si vous préférez utiliser un compte de service Google :
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=votre-compte-service@votre-projet.iam.gserviceaccount.com
EMAIL_PASSWORD=clé_privée_du_compte_service
```

## Configuration Outlook/Office 365

```bash
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USER=votre_email@outlook.com
EMAIL_PASSWORD=votre_mot_de_passe
```

## Configuration SendGrid (Alternative professionnelle)

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USER=apikey
EMAIL_PASSWORD=votre_clé_api_sendgrid
```

## Test de la configuration

Une fois configuré, lancez une analyse de marché depuis la page Settings. Le système enverra automatiquement :

1. **Le rapport complet** avec executive summary
2. **Les données de marché** (indices, commodities, crypto)
3. **L'analyse détaillée** (insights, risques, opportunités)
4. **Les sources** utilisées pour l'analyse

## Format de l'email

L'email sera envoyé en HTML avec :
- Design professionnel et responsive
- Executive summary en évidence
- Tableaux de données de marché
- Sections colorées pour insights, risques et opportunités
- Liens vers les sources

## Dépannage

### Erreur "Authentication failed"
- Vérifiez que `EMAIL_USER` et `EMAIL_PASSWORD` sont corrects
- Pour Gmail, utilisez un mot de passe d'application

### Erreur "Connection refused"
- Vérifiez `EMAIL_HOST` et `EMAIL_PORT`
- Assurez-vous que votre fournisseur SMTP autorise les connexions depuis Render

### Aucun email reçu
- Vérifiez `EMAIL_RECIPIENTS` (séparés par des virgules)
- Vérifiez vos spams
- Testez avec votre propre email d'abord
