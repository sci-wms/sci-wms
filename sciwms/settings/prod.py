#!python
# coding=utf-8
from .defaults import *

DEBUG          = False
TESTING        = False

ALLOWED_HOSTS  = ["*"]

LOGFILE = os.path.join(PROJECT_ROOT, "..", "logs", "sci-wms.log")
LOGGING = setup_logging(default='WARNING', logfile=LOGFILE)

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
