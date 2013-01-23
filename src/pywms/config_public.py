import multiprocessing
#import pywms.grid_init_script as grid
from netCDF4 import Dataset, num2date
import sys
from datetime import datetime
import os
import numpy as np

try:
    import gevent
    worker = "gevent"
except:
    try:
        import eventlet
        worker = "eventlet"
    except:
        # Default to basic sync worker if other libs are
        # not installed
        worker = "sync"

bind = "0.0.0.0:7000"
workers = multiprocessing.cpu_count()
worker_class = worker
debug = False
timeout = 120
#raceful_timeout = 120
max_requests = 2
keep_alive = 5
backlog = 100
log_file = 'sciwms_gunicorn.log'

def on_starting(server):
    #print os.environ
    #print os.getcwd()
    #import server_local_config
    #from grid_init_script import check_topology_age
    print '\n    ##################################################\n' +\
          '    #                                                #\n' +\
          '    #  Starting sci-wms...                           #\n' +\
          '    #  A wms server for unstructured scientific data #\n' +\
          '    #                                                #\n' +\
          '    ##################################################\n'
    #p = multiprocessing.Process(target=check_topology_age)
    #p.start()
