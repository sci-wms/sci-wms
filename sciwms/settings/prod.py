#!python
# coding=utf-8
from .defaults import *

DEBUG          = False
TESTING        = False

ALLOWED_HOSTS  = ["*"]

LOGGING = setup_logging(default='WARNING')

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
