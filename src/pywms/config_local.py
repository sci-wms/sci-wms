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
    
bind = "127.0.0.1:7000"
workers = 12#multiprocessing.cpu_count()
worker_class = worker
debug = True
timeout = 1000
max_requests = 16
backlog = 100
django_settings = "settings_local.py"


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
