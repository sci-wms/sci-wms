#!python
# coding=utf-8
from .defaults import *

DEBUG          = True
TESTING        = True

LOGGING = setup_logging(default='INFO')

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
