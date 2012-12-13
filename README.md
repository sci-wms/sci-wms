sci-wms
=========

####A Python WMS service for geospatial gridded data (Only unstructured FVCOM and ADCIRC grids and structured grids officially supported)

##System Requirements

- >= 4GB RAM
- > 2 CPU (> 4 CPU Best)
- Python > Version 2.6

##Roadmap

####Version 1:
- Bug free working implementation of the current dev code
- working getcaps
- working getmap
- working getlegendgraphic for non-autoscaling colormap styles
- service based dataset initialization and updating in addition to admin
- support for native Adcirc and FVCOM model output meshes

####Version 1.1:
- Support for rectilinear and curvilinear grids
- some wps functionality
- projections other than web mercator
- working getlegendgraphic response for the autoscaling colormap styles
- server-wide symbolization customization in admin

####Experimental Fork/Branch:
- Leverage hardware/opengl rendering for high overhead styles (facets, arrows...)

##Install

Download the compressed project and unpack anywhere. This is where the installation will live.

####If you have the standard enthought python distribution (epd):

Install the remaining dependencies:

    $easy_install gunicorn
    $easy_install greenlet
    $easy_install gevent              # or easy_install eventlet
    $easy_install django

####If are not using the enthought python distribution:

You must have the following installed:

- django
- gunicorn
- greenlet
- gevent or eventlet
- numpy
- matplotlib (1.1.0 preferred)
- matplotlib basemap (versions 1.0.1)
- netCDF4-python (netCDF4)
- shapely
- markdown

sci-wms works with both pip and virtualenv quite happily. If you
have pip installed you can use the following to install many (but not all) of the required modules:

    $pip install package

<!---
Or you can install the required packages (with the versions we develop
the wms on) with the requirements file:

    $pip install -r requirements.txt
-->

Similarly if you have setup_tools installed you can use:

    $easy_install package

If you are using virtualenv, just make sure you have the environment
activated before you try to install the packages or point to the environment
with pip on the install command.

You also need to ensure that you have basemap matplotlib toolkit installed:

    $wget -o basemap-1.0.1.tar.gz http://sourceforge.net/projects/matplotlib/files/matplotlib-toolkits/basemap-1.0.1/basemap-1.0.1.tar.gz/download
    $pip install basemap-1.0.1.tar.gz

##Run

####To Start With Django Development Server (on port 7000 for example):

    $cd project_folder/src/pywms

    $python manage.py runserver 0.0.0.0:7000   # for local use "localhost:7000"

####Run with Gunicorn Production WSGI Server:

    $cd project_folder/src/pywms

    $gunicorn_django -c config_public.py       # for local use config_local.py (configs use port 7000 by default)

or

    $cd project_folder
    $./start_server.sh    # this starts the public server
    $./stop_server.sh     # this stops the public server (actually ALL gunicorn_django processes)

You can edit the gunicorn config file (config_public.py and config_local.py) to specify the port and other
gunicorn server settings.

Can also be run with mod_wsgi/mod_python/etc in Apache. I prefer to proxypass
in Apache or nginx to the gunicorn server because I think its better setup
to handle the kinds of requests the server sees.

##Setup

###Change password for default user:

The default username is "*sciwmsuser*" and its password is "*sciwmspassword*". So,
the first thing you should do is login to the administration utility
and change the password or remove the default user and create a new one
for yourself.

The admin page can be found here:   http://server:port/admin

This admin site is how you will add and remove datasets for the wms server.

###http://server:port/wmstest

In order for the wmstest page to work you need to add your site (and port) url to the sites list and remove all others. This is *important* because a request to the *wmstest* page (or the http://server:port/update page) will
initialize newly added datasets and update datasets that are specified as updateable in the system. If you have a lot of datasets in your server, it may take a while to initialize all of them.
Ensure that there is a dataset_id.nc and dataset_id.domain file in the pywms folder for each of your unstructured datasets before allowing others to use your services. Initialization needs to only be done once
per dataset, and subsequent updates (if required) are quick. Structured grid datasets will only have a dataset_id.nc file in the pywms folder, they do not require the .domain file.

###Caveats:

Look at https://github.com/acrosby/sci-wms/issues?state=open for a list of known issues and problems.

###Use:

This wms server is based on a model that has a separate GetCapabilities endpoint and base wms end point
for each dataset added to the server. The datasets are distinguisghed internally by unique dataset id's
provided by the administrator. These id's are also used used in the base wms url as follows.

    http://server:port/wms/dataset_id/?REQUEST=GetCapabilities

There is no server-wide GetCapabilities document, but we may work on getting one installed in the future.

##Description of Styles Parameter:

STYLES=position1_position2_position3_position4_position5_position6_position7

###Position 1
This is the style of image to return.
For node variables the options are: pcolor, facets, contours, filledcontours, (vectors or barbs if specifying two variables like LAYERS=u,v)

For cell variables the options are: pcolor, facets, contours, filledcontours, (vectors or barbs if specifying two variables like LAYERS=u,v)

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

