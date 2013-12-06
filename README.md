#sci-wms

COPYRIGHT 2010 RPS ASA
    
    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.

####A Python WMS service for geospatial gridded data

##System Requirements

- >= 4GB RAM But it depends directly on the size and extents of the datasets you will be visualizing.
- > 2 CPU (> 4 CPU Better) 
- Python 2.7.x with sqlite
- LibGeos (http://download.osgeo.org/geos/)
- LibSpatialIndex (http://libspatialindex.github.com)
- netCDF4 C library (with opendap enabled, if opendap/remote functionality is desired)
- libhdf5 C library (dependency of netCDF4)
- libcurl (required for opendap)

Your system may have already installed the following dependencies, but 
they are required by some of the module dependencies installed in the next section.

- libpng
- libfreetype
- libjpeg
- libevent

##Community

[We have started a Google Group for the sci-wms project located here.](https://groups.google.com/forum/?fromgroups#!forum/sci-wms)

##Installation

[Download the compressed project and unpack anywhere.](http://acrosby.github.com/sci-wms) This is where the installation will live.

Install the following Python dependencies using `pip`, `easy_install`, or equivalent. 
If you are using [virtualenv](http://www.virtualenv.org/en/latest/), just make 
sure you have the environment
activated before you try to install the packages or point to the environment
with pip on the install command.
```bash
pip install numpy
pip install Django==1.4.0
pip install Shapely
pip install greenlet>=0.3.1
pip install gevent>=0.13.6
pip install gunicorn>=0.13.4
pip install matplotlib>=1.2.0
pip install netCDF4>=1.0.2
pip install rtree
pip install south
```

You also need to ensure that you have basemap matplotlib toolkit installed, 
which isn't available from pypi.
```bash
wget http://sourceforge.net/projects/matplotlib/files/matplotlib-toolkits/basemap-1.0.6/basemap-1.0.6.tar.gz
pip install basemap-1.0.6.tar.gz
```

If your version of the HDF5 C libraries is >=1.8.10, you may have to install 
the netCDF4 Python module from the source repository in order for it to work properly. 
This requires an SVN client to be installed on your system. (Please let us know if 
you have problems importing netCDF4 in Python after running this command.)
```bash
pip install -e svn+http://netcdf4-python.googlecode.com/svn/trunk#egg=netCDF4
```

If your NetCDF4 and HDF5 libraries are in non-typical locations, you will need to pass the locations to the `pip` command:
```bash
NETCDF4_DIR=path HDF5_DIR=path pip install netCDF4
```

If there is problem with gevent or greenlet, or if you would like gunicorn 
to use an alternative worker, you can install the `eventlet` worker. With some configuration 
of the sci-wms gunicorn configuration files,  you can also use `tornado` workers.

```bash
pip install eventlet
pip install tornado
```

##Test
To make sure that dependencies have been installed correctly, and that sci-wms is fully functional. 
Run the following command to run the tests.
```bash
cd sci-wms/src/pywms && python manage.py test
```

##Start the services
You can start the services on port 7000 from the command line by using the following commands. [Learn about gunicorn wsgi server configuration by clicking here.](http://gunicorn.org/)
```bash
cd sci-wms/src/pywms && gunicorn_django -c config_public.py
```

##Caveats:

Look at [https://github.com/asascience-open/sci-wms/issues?state=open](https://github.com/asascience-open/sci-wms/issues?state=open) for a list of known issues and problems.
