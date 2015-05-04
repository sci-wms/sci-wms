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
    import tornado
    worker = "tornado"
except:
    try:
        import eventlet
        worker = "eventlet"
    except:
        try:
            import gevent
            worker = "gevent"
        except:
            # Default to basic sync worker if other libs are
            # not installed
            worker = "sync"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sciwms.settings.prod")

bind              = "127.0.0.1:7002"
workers           = multiprocessing.cpu_count() + 1
worker_class      = worker
debug             = False
timeout           = 30
#graceful_timeout = 120
max_requests      = 20
keepalive         = 5
backlog           = 20
accesslog         = os.path.abspath(os.path.join(os.path.dirname(__file__), "logs", "gunicorn_access.log"))
errorlog          = os.path.abspath(os.path.join(os.path.dirname(__file__), "logs", "gunicorn_error.log"))
loglevel          = "warning"
preload_app       = False
proc_name         = "sciwms"
