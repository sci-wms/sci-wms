#!python
# coding=utf-8
import os
from .defaults import *  # noqa
from redis import ConnectionPool

DEBUG          = False
TESTING        = False

TEMPLATES[0]['OPTIONS']['debug'] = False

ALLOWED_HOSTS  = ["*"]

LOGFILE = os.path.join(BASE_DIR, "logs", "sci-wms.log")
LOGGING = setup_logging(default='WARNING', logfile=LOGFILE)


DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('POSTGRES_DB', 'sciwms'),
        'USER':     os.environ.get('POSTGRES_USER', 'sciwms'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'sciwms'),
        'HOST':     os.environ.get('POSTGRES_HOST', 'db'),
        'PORT':     os.environ.get('POSTGRES_PORT', 5432),
    },
}

# Redis
redis_host = os.environ.get('REDIS_HOST', 'redis')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_db = int(os.environ.get('REDIS_DB', 0))

pool = ConnectionPool(host=redis_host, port=redis_port, db=redis_db)

# Huey
HUEY = {
    'name': 'sciwms',
    'results': True,  # Store return values of tasks.
    'store_none': True,  # If a task returns None, do not save to results.
    'immediate': False,  # If DEBUG=True, run synchronously.
    'huey_class': 'huey.RedisHuey',  # Use path to redis huey by default,
    'blocking': False,  # Poll the queue rather than do blocking pop.
    'connection': {
        'connection_pool': pool
    },
    'consumer': {
        'workers': 4,
        'worker_type': 'process',
        'quiet': True,
        'verbose': False,
        'initial_delay': 0.1,  # Smallest polling interval, same as -d.
        'backoff': 1.15,  # Exponential backoff using this rate, -b.
        'max_delay': 10.0,  # Max possible polling interval, -m.
        'utc': True,  # Treat ETAs and schedules as UTC datetimes.
        'scheduler_interval': 5,  # Check schedule every second, -s.
        'periodic': True,  # Enable crontab feature.
        'check_worker_health': True,  # Enable worker health checks.
        'health_check_interval': 30,  # Check worker health every second.
    },
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'TIMEOUT': None,
        'LOCATION': '{}:{}'.format(redis_host, redis_port),
        'OPTIONS': {
            'DB' : redis_db + 2,
            'PARSER_CLASS': 'redis.connection.HiredisParser',   
        }
    },
    'page': {
        'BACKEND': 'redis_cache.RedisCache',
        'TIMEOUT': 300,
        'LOCATION': '{}:{}'.format(redis_host, redis_port),
        'OPTIONS': {
            'DB' : redis_db + 3,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    },
    'time': {
        'BACKEND': 'redis_cache.RedisCache',
        'TIMEOUT': 300,
        'LOCATION': '{}:{}'.format(redis_host, redis_port),
        'OPTIONS': {
            'DB' : redis_db + 4,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    },
    'topology': {
        'BACKEND': 'redis_cache.RedisCache',
        'TIMEOUT': 300,
        'LOCATION': '{}:{}'.format(redis_host, redis_port),
        'OPTIONS': {
            'DB' : redis_db + 5,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}

LOCAL_APPS = []
try:
    from local_settings import *  # noqa
except ImportError:
    pass
try:
    from local.settings import *  # noqa
except ImportError:
    pass
INSTALLED_APPS += LOCAL_APPS
