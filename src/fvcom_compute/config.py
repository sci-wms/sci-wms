import multiprocessing
bind = "localhost:7000"
workers = 12#multiprocessing.cpu_count()
worker_class = "gevent"
debug = True
timeout = 15
max_requests = 50
backlog = 1000

#name = "unstructuredserver"
