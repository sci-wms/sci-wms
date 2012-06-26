import multiprocessing
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
workers = 12#multiprocessing.cpu_count()
worker_class = worker
debug = True
timeout = 1000
max_requests = 16
backlog = 100
#preload = True


