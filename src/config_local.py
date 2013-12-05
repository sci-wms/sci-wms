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

import os
import sys
import multiprocessing

try:
    import eventlet
    worker = "eventlet"
except:
    try:
        import greenlet
        worker = "greenlet"
    except:
        try:
            import gevent
            worker = "gevent_wsgi"
        except:
            # Default to basic sync worker if other libs are
            # not installed
            worker = "sync"

bind = "127.0.0.1:7000"
workers = multiprocessing.cpu_count()
worker_class = worker
debug = True
timeout = 1000
max_requests = 2
backlog = 5
django_settings = "pywms.settings"
log_file = 'sciwms_gunicorn.log'
os.environ['DJANGO_SETTINGS_MODULE'] = "pywms.settings"


def on_starting(server):
    sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))

    print "Initializing datasets topologies..."
    from pywms.grid_init_script import init_all_datasets
    init_all_datasets()

    print '\n    ##################################################\n' +\
          '    #                                                #\n' +\
          '    #  Starting sci-wms...                           #\n' +\
          '    #  A wms server for unstructured scientific data #\n' +\
          '    #                                                #\n' +\
          '    ##################################################\n'
