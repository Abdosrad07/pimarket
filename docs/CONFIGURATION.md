# Configuration de Pi Market

Aucune variable d'environnement n'est **obligatoire** : l'application démarre avec des
valeurs par défaut sûres (SQLite, cache mémoire, paiements en mode démo). Pour
personnaliser la configuration, créez un fichier `.env` à la racine en copiant
les variables ci-dessous.

## Général

| Variable | Défaut | Description |
|---|---|---|
| `DEBUG` | `True` | Mode debug Django. Mettre `False` en production. |
| `SECRET_KEY` | clé de dev | Clé secrète Django. **Obligatoire à changer en production.** |
| `ALLOWED_HOSTS` | `*` | Hôtes autorisés, séparés par des virgules. |

## Base de données

| Variable | Défaut | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Ex. `postgresql://user:pass@host:5432/pimarket` |

## Redis (optionnel)

Sans Redis, le cache, les channels WebSocket et Celery basculent automatiquement
sur des implémentations en mémoire (les tâches Celery deviennent synchrones).

| Variable | Défaut | Description |
|---|---|---|
| `REDIS_URL` | *(vide)* | Ex. `redis://localhost:6379/0` |

## Paiements

| Variable | Défaut | Description |
|---|---|---|
| `DEMO_PAYMENTS` | `True` | Paiements simulés localement : le parcours d'achat fonctionne sans aucune clé. |
| `STRIPE_SECRET_KEY` | *(vide)* | Clé Stripe. Si vide + `DEMO_PAYMENTS=False`, les paiements fiat échouent. |
| `STRIPE_PUBLISHABLE_KEY` | *(vide)* | Clé publique Stripe. |
| `STRIPE_WEBHOOK_SECRET` | *(vide)* | Secret de webhook Stripe. |
| `PI_API_KEY` / `PI_API_SECRET` | *(vide)* | Credentials Pi Network. |
| `PI_WEBHOOK_SECRET` | *(vide)* | Secret de webhook Pi Network. |

Pour activer de vrais paiements : `DEMO_PAYMENTS=False` + clés Stripe/Pi valides.

## SMS (OTP)

| Variable | Défaut | Description |
|---|---|---|
| `SMS_PROVIDER` | `mock` | `mock` imprime les OTP dans la console ; `twilio` envoie de vrais SMS. |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER` | *(vide)* | Credentials Twilio. |

## CORS

| Variable | Défaut | Description |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | *(vide)* | Origines séparées par des virgules, ex. `https://mon-domaine.com` |

## Stockage média (production)

| Variable | Défaut | Description |
|---|---|---|
| `AWS_STORAGE_BUCKET_NAME` | *(vide)* | Si défini (avec `DEBUG=False`), les médias vont sur S3. |
| `AWS_S3_REGION_NAME` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | *(vide)* | Credentials AWS. |

## Lancement

```bash
pip install -r requirements/base.txt
python manage.py migrate
python manage.py seed_demo_data   # données démo + comptes (idempotent)
python manage.py runserver        # ou gunicorn via le Procfile
```

Comptes démo (mot de passe `demo1234`) :

- Acheteur : `+221000000002`
- Vendeuse : `+221000000001` (boutiques Tech Paradise et Fashion Hub)
- Admin : `+221000000000` → `/admin/`
