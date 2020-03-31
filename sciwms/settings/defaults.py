#!python
# coding=utf-8
import os

import matplotlib

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR = os.path.dirname(PROJECT_ROOT)

DEBUG = False

ADMINS = ()
MANAGERS = ADMINS
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "notasecret!")

TESTING            = False
ROOT_URLCONF       = 'sciwms.urls'
WSGI_APPLICATION   = 'sciwms.wsgi.application'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
LANGUAGE_CODE      = 'en-us'
TIME_ZONE          = 'UTC'
USE_I18N           = False
USE_L10N           = False
USE_TZ             = True
STATIC_URL         = '/static/'
STATIC_ROOT        = os.path.abspath(os.path.join(BASE_DIR, "static"))
MEDIA_URL          = '/media/'
MEDIA_ROOT         = os.path.abspath(os.path.join(BASE_DIR, "media"))

INSTALLED_APPS = [
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'wms',
    'wmsrest',
    'rest_framework',
    'huey.contrib.djhuey',
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'wms.context_processors.globals'
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_ACCESS': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
}


# Logging
def setup_logging(default, logfile):
    if not os.path.exists(os.path.dirname(logfile)):
        os.makedirs(os.path.dirname(logfile))

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'backupCount': 5,
                'maxBytes': 1024 * 1024 * 20,  # 20MB
                'filename': logfile,
                'formatter': 'verbose'
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file', 'console'],
                'level': default,
                'propagate': True,
            },
            'huey': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'pyugrid': {
                'handlers': ['file', 'console'],
                'level': 'WARNING',
            },
            '': {
                'handlers': ['file', 'console'],
                'level': default,
            }
        }
    }


# Where to store the Topology data?
TOPOLOGY_PATH = os.environ.get('TOPOLOGY_PATH', os.path.join(BASE_DIR, "wms", "topology"))
if not os.path.exists(TOPOLOGY_PATH):
    os.makedirs(TOPOLOGY_PATH)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sciwms-default-cache',
    },
    'page': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    },
    'time': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': TOPOLOGY_PATH
    },
    'topology': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': TOPOLOGY_PATH
    }
}

db_path = os.environ.get('SQLITE_DB_PATH', os.path.join(PROJECT_ROOT, "db"))
if not os.path.isdir(db_path):
    os.makedirs(db_path)
db_file = os.path.join(db_path, "sci-wms.db")
huey_file = os.path.join(db_path, "huey.db")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':  db_file,
    }
}

# Grappelli
GRAPPELLI_ADMIN_TITLE = 'sci-wms'

# Matplotlib
matplotlib.use("Agg")

HUEY = {
    'name': 'sciwms',
    'filename': huey_file,
    'result_store': True,  # Store return values of tasks.
    'events': True,  # Consumer emits events allowing real-time monitoring.
    'store_none': True,  # If a task returns None, do not save to results.
    'immediate': True,  # If DEBUG=True, run synchronously.
    'store_errors': True,  # Store error info if task throws exception.
    'blocking': False,  # Poll the queue rather than do blocking pop.
    'backend_class': 'huey.SqliteHuey',  # Use path to redis huey by default,
}
