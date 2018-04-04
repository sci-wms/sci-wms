#!python
# coding=utf-8
import os
from .defaults import *  # noqa

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
        'HOST':     os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT':     os.environ.get('POSTGRES_PORT', 5432),
    },
}

# Redis
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6060))
redis_db = int(os.environ.get('REDIS_DB', 0))

# Celery
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
