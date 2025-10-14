# Production Deployment Guide

## Prerequisites

- Ubuntu 20.04+ server
- Domain name configured
- At least 2GB RAM, 20GB disk space
- Root or sudo access

## Quick Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Clone and Configure

```bash
# Clone repository
cd /var/www
sudo git clone <your-repo-url> pimarket
cd pimarket

# Set permissions
sudo chown -R $USER:$USER /var/www/pimarket

# Create production .env
cp .env.example .env
nano .env
```

### 3. Configure Environment Variables

Edit `.env` with production values:

```bash
DEBUG=False
SECRET_KEY=<generate-with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DATABASE_URL=postgresql://pimarket:STRONG_PASSWORD@db:5432/pimarket_prod
REDIS_URL=redis://redis:6379/0

# Production Stripe keys
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Production Pi Network keys
PI_API_KEY=your_production_pi_api_key
PI_API_SECRET=your_production_pi_api_secret
PI_WEBHOOK_SECRET=your_production_pi_webhook_secret

# Production SMS provider
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 4. Build and Start Services

```bash
# Build containers
docker-compose -f docker-compose.yml build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec django python manage.py migrate

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput

# Create superuser
docker-compose exec django python manage.py createsuperuser
```

### 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/pimarket
```

Add this configuration:

```nginx
upstream django {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    client_max_body_size 20M;
    
    location /static/ {
        alias /var/www/pimarket/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/pimarket/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/pimarket /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Setup SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts. Certbot will automatically configure SSL.

### 7. Configure Webhooks

#### Stripe Webhooks

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. URL: `https://yourdomain.com/webhooks/stripe/`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.captured`
   - `charge.refunded`
5. Copy the webhook signing secret and add to `.env`

#### Pi Network Webhooks

1. Go to Pi Network Developer Portal
2. Configure webhook URL: `https://yourdomain.com/webhooks/pi/`
3. Copy webhook secret and add to `.env`

### 8. Setup Monitoring

#### Systemd Service (Alternative to Docker Compose)

If you prefer systemd:

```bash
sudo nano /etc/systemd/system/pimarket.service
```

```ini
[Unit]
Description=Pi Market Django Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/pimarket
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable pimarket
sudo systemctl start pimarket
```

#### Logs with Logrotate

```bash
sudo nano /etc/logrotate.d/pimarket
```

```
/var/log/pimarket/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

### 9. Backup Strategy

#### Database Backup Script

```bash
nano /var/www/pimarket/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/pimarket"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U pimarket pimarket_prod | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and add to crontab:

```bash
chmod +x /var/www/pimarket/backup.sh
crontab -e
```

Add:
```
0 2 * * * /var/www/pimarket/backup.sh >> /var/log/pimarket-backup.log 2>&1
```

### 10. Performance Optimization

#### PostgreSQL Tuning

```bash
docker-compose exec db psql -U pimarket -d pimarket_prod
```

```sql
-- Increase work_mem for better query performance
ALTER SYSTEM SET work_mem = '16MB';

-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Reload configuration
SELECT pg_reload_conf();
```

#### Redis Configuration

Edit `docker-compose.yml` to add Redis maxmemory:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 11. Security Hardening

#### Firewall Setup

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

#### Fail2ban

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### Regular Updates

```bash
# Create update script
nano /var/www/pimarket/update.sh
```

```bash
#!/bin/bash
cd /var/www/pimarket

# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Run migrations
docker-compose exec django python manage.py migrate

# Collect static
docker-compose exec django python manage.py collectstatic --noinput

# Restart services
docker-compose restart django celery_worker celery_beat

echo "Update completed"
```

### 12. Monitoring with Uptime Checks

Use external services:
- UptimeRobot (free)
- Pingdom
- StatusCake

Configure alerts for:
- Website down
- API response time > 2s
- SSL certificate expiring

### 13. Error Tracking (Optional)

#### Sentry Integration

Add to `requirements/prod.txt`:
```
sentry-sdk==1.38.0
```

Add to `settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn="your-sentry-dsn",
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True
    )
```

### 14. Health Check Endpoint

Add to `pimarket/urls.py`:

```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy'})

urlpatterns = [
    path('health/', health_check),
    # ... other patterns
]
```

### 15. Verify Deployment

```bash
# Check services are running
docker-compose ps

# Check Django logs
docker-compose logs -f django

# Check Celery is processing
docker-compose logs -f celery_worker

# Test API
curl https://yourdomain.com/health/

# Test SSL
curl -I https://yourdomain.com

# Check database connection
docker-compose exec django python manage.py dbshell
```

## Troubleshooting

### Service won't start
```bash
docker-compose logs django
docker-compose restart django
```

### Database connection issues
```bash
docker-compose exec db psql -U pimarket -d pimarket_prod
```

### Celery not processing tasks
```bash
docker-compose logs celery_worker
docker-compose restart celery_worker celery_beat
```

### SSL certificate renewal
```bash
sudo certbot renew --dry-run
```

## Scaling Strategy

### Horizontal Scaling

1. **Multiple Django instances:**
   - Use Docker Swarm or Kubernetes
   - Load balancer (HAProxy/Nginx)

2. **Database Read Replicas:**
   - PostgreSQL streaming replication
   - Configure Django for read/write splitting

3. **Redis Cluster:**
   - Redis Cluster for high availability
   - Sentinel for automatic failover

4. **Celery Workers:**
   - Separate workers for different queues
   - Auto-scaling based on queue length

### CDN for Static Files

Use AWS S3 + CloudFront or Cloudflare:

```python
# settings.py
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

## Maintenance Mode

Create `maintenance.html` and configure Nginx:

```nginx
if (-f /var/www/pimarket/maintenance.flag) {
    return 503;
}

error_page 503 @maintenance;
location @maintenance {
    root /var/www/pimarket;
    rewrite ^(.*)$ /maintenance.html break;
}
```

Enable maintenance:
```bash
touch /var/www/pimarket/maintenance.flag
```

Disable maintenance:
```bash
rm /var/www/pimarket/maintenance.flag
```

## Post-Deployment Checklist

- [ ] All services running
- [ ] SSL certificate valid
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Webhooks configured
- [ ] Backups scheduled
- [ ] Monitoring configured
- [ ] Firewall enabled
- [ ] Health check passing
- [ ] API endpoints responding
- [ ] Payment providers tested
- [ ] SMS notifications working
- [ ] Admin panel accessible
- [ ] Error tracking configured

---

**Your Pi Market is now live! 🚀**