'''
COPYRIGHT 2010 Alexander Crosby

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

import multiprocessing, sys, os

# Default to basic sync worker if other libs are
# not installed
worker = "sync"
try:
    import tornado
    worker = "tornado"
try:
    import eventlet
    worker = "eventlet"
try:
    import greenlet
    worker = "greenlet"
try:
    import gevent
    worker = "gevent"

bind = "0.0.0.0:7000"
workers = multiprocessing.cpu_count() + 1
worker_class = worker
debug = False
timeout = 120
#raceful_timeout = 120
max_requests = 20
keep_alive = 5
backlog = 10
access_logfile = 'sciwms_gunicorn.log'

def on_starting(server):
    print '\n    ##################################################\n' +\
          '    #                                                #\n' +\
          '    #  Starting sci-wms...                           #\n' +\
          '    #  A wms server for unstructured scientific data #\n' +\
          '    #                                                #\n' +\
          '    ##################################################\n'
