FROM python:3.12-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Répertoire de travail
WORKDIR /app

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "flask_gpt5_integration_final.py"]
