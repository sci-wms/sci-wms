import multiprocessing

bind = "0.0.0.0:7000"
workers = 12#multiprocessing.cpu_count()
worker_class = "gevent"
debug = True
timeout = 1000
max_requests = 8
backlog = 100

#name = "unstructuredserver"
