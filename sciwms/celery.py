# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
from datetime import timedelta

from celery import Celery
from django.conf import settings  # noqa

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sciwms.settings.dev')

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6060))
redis_db = int(os.environ.get('REDIS_DB', 0))
broker = 'redis://{}:{}/{}'.format(redis_host, redis_port, redis_db)
results = 'redis://{}:{}/{}'.format(redis_host, redis_port, redis_db + 1)

eager = settings.DEBUG

app = Celery('sciwms')
app.conf.update(dict(
    accept_content=['json'],
    beat_schedule={
        'regulate': {
            'task': 'wms.tasks.regulate',
            'schedule': timedelta(minutes=5)
        }
    },
    broker_transport_options={
        'fanout_patterns': True, 'fanout_prefix': True
    },
    broker_url=broker,
    imports=('wms.tasks', ),
    result_backend=results,
    result_serializer='json',
    task_always_eager=eager,
    task_hard_time_limit = 7200,
    task_serializer='json',
    task_soft_time_limit=7200,
    timezone='UTC',
    worker_max_tasks_per_child=500,
    worker_prefetch_multiplier=1,
))
