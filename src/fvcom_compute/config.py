import multiprocessing
bind = "localhost:7000"
workers = multiprocessing.cpu_count()
worker_class = "gevent"
debug = True
timeout = 60
max_requests = 4
backlog = 100

#name = "unstructuredserver"
