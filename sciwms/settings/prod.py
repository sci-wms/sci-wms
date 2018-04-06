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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sciwms-default-cache',
    },
    'page': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sciwms-page-cache',
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
