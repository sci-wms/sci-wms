pywms
=========

##Install

####If you have the standard enthought python distribution (epd):

Install the remaining dependencies:

    $easy_install gunicorn
    $easy_install greenlet
    $easy_install gevent              # or easy_install eventlet
    $easy_install django
    $easy_install pp                  # http://www.parallelpython.com

You also must install a netCDF4-python (preferrably opendap enabled):

https://code.google.com/p/netcdf4-python/

####If are not using the enthought python distribution:

You must have the following installed:

- django
- gunicorn
- greenlet
- gevent or eventlet
- numpy
- matplotlib
- matplotlib-basemap
- netCDF4-python
- shapely
- pp (parallelpython)

pywms works with both pip and virtualenv quite happily. If you
have pip installed you can use:

    $pip install package
    
for many of the dependent modules. Similarly if you have setup_tools
installed you can use:

    $easy_install package
    
If you are using virtualenv, just make sure you have the environment
activated before you try to install the packages or point to the environment
with pip on the install command.

##Setup

Add the local ip or domain for the service in the **server_local_config.py**
file so that the /wmstest/ page works.

The service comes with a sample dataset setup, but you can remove and add your own
local files or OpenDAP endpoints.

##Run

####To Start With Django Development Server:

    $cd project_folder/src/pywms

    $python manage.py runserver 0.0.0.0:7000   # for local use "localhost:7000"

####To Start With Production WSGI Server:

    $cd project_folder/src/pywms

    $gunicorn_django -c config_public.py       # for local use config_local.py

You can edit the gunicorn config file to specify the port and other
gunicorn settings.

Can also be run with mod_wsgi in Apache. I prefer to proxypass
in Apache to the gunicorn server because I think its better setup
to handle the kinds of requests the server sees.

