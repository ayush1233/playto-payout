import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
# Defaults to development if not set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playto.settings.development')

app = Celery('playto')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.broker_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.conf.result_backend = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Register Celery Beat schedule in the Django database
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
