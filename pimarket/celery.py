import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pimarket.settings')

app = Celery('pimarket')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'check-pending-payments': {
        'task': 'apps.payments.tasks.check_pending_payments',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'auto-release-escrow': {
        'task': 'apps.payments.tasks.auto_release_escrow',
        'schedule': crontab(hour='0', minute='0'),  # Daily at midnight
    },
}