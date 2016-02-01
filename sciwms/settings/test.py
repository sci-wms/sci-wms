#!python
# coding=utf-8
from .defaults import *

DEBUG          = True
TESTING        = True

LOGFILE = os.path.join(BASE_DIR, "logs", "sci-wms.log")
LOGGING = setup_logging(default='INFO', logfile=LOGFILE)

# Where to store the Topology data?
TOPOLOGY_PATH = os.path.join(BASE_DIR, "wms", "tests", "topology")
if not os.path.exists(TOPOLOGY_PATH):
    os.makedirs(TOPOLOGY_PATH)

LOCAL_APPS = []
try:
    from local_settings import *
except ImportError:
    pass
try:
    from local.settings import *
except ImportError:
    pass
INSTALLED_APPS += LOCAL_APPS
