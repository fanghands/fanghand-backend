from celery import Celery
from celery.schedules import crontab

# Use env vars with defaults for broker/backend
import os
BROKER = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

celery = Celery(
    'fanghand',
    broker=BROKER,
    backend=BACKEND,
    include=[
        'app.workers.tasks.hand_tasks',
        'app.workers.tasks.burn_tasks',
        'app.workers.tasks.payout_tasks',
        'app.workers.tasks.sync_tasks',
    ]
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_soft_time_limit=300,
    task_time_limit=360,
    beat_schedule={
        'monitor-agents': {
            'task': 'monitor_agent_health',
            'schedule': crontab(minute='*/5'),
        },
        'sync-fgh-balances': {
            'task': 'sync_fgh_balances',
            'schedule': crontab(minute='*/15'),
        },
        'monthly-payouts': {
            'task': 'process_monthly_payouts',
            'schedule': crontab(day_of_month='1', hour='0', minute='0'),
        },
    }
)
