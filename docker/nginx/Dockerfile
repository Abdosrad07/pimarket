from nginx:alpine

# Supprimer la configuration par défaut
RUN rm /etc/nginx/conf.d/default.conf

# Copier notre configuration personnalisée
COPY docker/nginx/nginx.conf /etc/nginx/conf

# Copier le fichier de validation directement dans le dossier web racine de Nginx
COPY public/validation-key.txt /usr/share/nginx/html/validation-key.txt