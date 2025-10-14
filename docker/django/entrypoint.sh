#!/bin/sh

# Attendre que la base de données soit prête
# Note: netcat est installé dans le Dockerfile
echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

# Appliquer les migrations de la base de données
python manage.py migrate

# Lancer la commande passée au conteneur
exec "$@"