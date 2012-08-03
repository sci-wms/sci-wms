sci-wms
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
- matplotlib (1.1.0 preferred)
- matplotlib basemap (versions 1.0.2+ require mpl-toolkit axisgrid to be installed as well, but perhaps only if you are using mpl 1.1.0...)
- netCDF4-python (netCDF4)
- shapely
- pp (parallelpython)

pywms works with both pip and virtualenv quite happily. If you
have pip installed you can use the following to install many (but not all) of the required modules:

    $pip install package

Or you can install the required packages (with the versions we develop
the wms on) with the requirements file:

    $pip install -r requirements.txt
    
Similarly if you have setup_tools installed you can use:

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
in Apache or nginx to the gunicorn server because I think its better setup
to handle the kinds of requests the server sees.


##Description of Styles Parameter:

STYLES=position1_position2_position3_position4_position5_position6_position7

###Position 1
This is the type of image to return.
For node variables the options are: pcolor, facets, contours, filledcontours, interpolate

For cell variables the options are: pcolor, facets, contours, filledcontours, (vectors if specifying two variables like LAYERS=u,v)

###Position 2
This is the type of processing to do if the request has a time range specified instead of one time. (Probably won’t be needed for this project, but) The options are either: average or maximum

###Position 3
This is the colormap to be used. Case-sensitive match to the matplotlib default colormaps. Possible values can be found here: http://www.scipy.org/Cookbook/Matplotlib/Show_colormaps

To use colormaps that contain an underscore ( “_” ) substitute the underscore for a hyphen ( “-”) in the styles parameter.

###Position 4
For the color scaling, this value is the lower limit or “cmin”, should be entered as an integer or decimal number. If either cmin or cmax are listed as None then the colormap will autoscale to the available data.

###Position 5
For color scaling, this value is the upper limit, or “cmax”, should be entered as an integer or decimal number. If either cmin or cmax are listed as None then the colormap will autoscale to the available data.

###Position 6
This value specifies whether the variable input in LAYERS parameter is in the middle of an unstructured cell or if it is on the node/vertex. Allowable values in this position are either: cell or node

###Position 7
This is a case-sensitive boolean to say whether or not the absolute value (magnitude) or the actual value should be taken if only one variable is specified in LAYERS=

For instance LAYERS=u will return positive and negative values if the value in Position 7 is set to False, but if it set to True, the magnitude of u will be returned.

Allowable values: True or False
(in the case of vectors, True = autoscaling of vectors, False means no autoscaling of vectors with default scale) If there is a number in this position, the number is taken as the scale. Start with 2 and adjust from there.

