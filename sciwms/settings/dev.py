'''
COPYRIGHT 2010 RPS ASA

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

from .defaults import *

DEBUG          = True
TEMPLATE_DEBUG = True
TESTING        = False

LOGFILE = os.path.join(PROJECT_ROOT, "..", "logs", "sci-wms.log")
if not os.path.exists(os.path.dirname(LOGFILE)):
    os.makedirs(os.path.dirname(LOGFILE))

LOGGING = {
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
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'backupCount': 5,
            'maxBytes': 1024*1024*20,  # 20MB
            'filename': LOGFILE,
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'DEBUG',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'WARNING',
            'propagate': True,
        },
        'sci-wms': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'wms': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar'
]

LOCAL_APPS = ()
try:
    from local_settings import *
except ImportError:
    pass
try:
    from local.settings import *
except ImportError:
    pass
INSTALLED_APPS += LOCAL_APPS
