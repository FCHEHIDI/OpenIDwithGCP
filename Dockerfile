# Utiliser Python 3.11 slim pour une image légère
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port (Cloud Run utilise la variable PORT)
ENV PORT=8080

# Démarrer l'application avec uvicorn
# Cloud Run fournit la variable d'environnement PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
