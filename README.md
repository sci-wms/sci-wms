fvcom_wms
=========

Install
_______
###If you have the standard enthought python distribution (epd):

Install the remaining dependencies:

    $easy_install gunicorn
    $easy_install greenlet
    $easy_install gevent              # or easy_install eventlet
    $easy_install django
    $easy_install pp                  # http://www.parallelpython.com

You also must install a netCDF4-python (preferrably opendap enabled):

https://code.google.com/p/netcdf4-python/

###If are not using the enthought python distribution:

You must have the following installed:

- django
- gunicorn
- numpy
- matplotlib
- matplotlib-basemap
- netCDF4-python
- shapely
- pp (parallelpython)


Run
___
###To Start With Django Development Server:

$cd fvcom_wms/src/fvcom_compute

$python manage.py runserver 0.0.0.0:7000

###To Start With Production WSGI Server:

$cd fvcom_wms/src/fvcom_compute

$gunicorn_django -c config.py


Notes:
______
For the server to work correctly, you must edit the 
server_local_config.py file. Add the full paths to YOUR
installation of the service, and edit the list of datasets
to include an id and path or opendap link to your dataset.
