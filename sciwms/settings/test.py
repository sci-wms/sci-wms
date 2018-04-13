#!python
# coding=utf-8
import os
from .defaults import *  # noqa

DEBUG          = True
TESTING        = True

LOGFILE = os.path.join(BASE_DIR, "logs", "sci-wms.log")
LOGGING = setup_logging(default='INFO', logfile=LOGFILE)

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
