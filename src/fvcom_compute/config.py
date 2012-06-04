import multiprocessing
bind = "0.0.0.0:7000"
workers = 6#multiprocessing.cpu_count()
worker_class = "gevent"
debug = True
timeout = 50
max_requests = 1
backlog = 100

#name = "unstructuredserver"
