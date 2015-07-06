#sci-wms  [![Build Status](https://travis-ci.org/sci-wms/sci-wms.svg)](https://travis-ci.org/sci-wms/sci-wms)
####A Python WMS service for geospatial gridded data


##System Requirements

- \>= 4GB RAM But it depends directly on the size and extents of the datasets you will be visualizing.
- \> 2 CPU (> 4 CPU Better)
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

Issues/Discussion: https://github.com/sci-wms/sci-wms/issues


##Installation

[Download the compressed project](https://github.com/sci-wms/sci-wms) and unpack or clone this github project into the location the installation will run: `git clone https://github.com/sci-wms/sci-wms.git`.


## Developing

### Testing
To make sure that dependencies have been installed correctly, and that sci-wms is fully functional.
Run the following command from the root sci-wms directory to run the tests.
```bash
pip install -r requirements-test.txt
py.test -s
```

### Running
You can start a development/testing service on port 8000 from the command line by using the following command.
```bash
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver_plus
```

## Deployment

### Setup
```bash
pip install -r requirements-prod.txt
DJANGO_SETTINGS_MODULE=sciwms.settings.prod python manage.py migrate
```

### Start the services
You should NOT run the development service on a production server!  You will need to run all production sci-wms application servers using gunicorn. [Learn about gunicorn wsgi server configuration by clicking here](http://gunicorn.org/).
A helper script for starting a gunicorn sci-wms server is included with the source.  To manage the service, you may use two helper scripts included with sci-wms:
```bash
bash start_server.sh
```
and
```bash
bash stop_server.sh
```

`start_server.sh` loads the config file `gunicorn_config_prod.py` that is in the root of the sci-wms source tree.  Please look at the gunicorn documentation for additional config options and edit this file as necessary.

### Configuring the deployment
You should edit the `sciwms/settings/local_settings.py` file (may need to create it) after deployment and add the following:
```python
# Specific host(s) that that server should be accessible on
ALLOWED_HOSTS  = ["sciwms.external-host.com", "YOUR_IP_ADDRESS", "sciwms.internal-host"]

# Sci-wms caches data on disk so it does not have to read static data from each dataset every request.
# By default, the path is `SCIWMS_ROOT/sciwms/apps/wms/topology`.
TOPOLOGY_PATH = "/data/sci-wms-topology"
if not os.path.exists(TOPOLOGY_PATH):
    os.makedirs(TOPOLOGY_PATH)
```

##Caveats:

Look at [https://github.com/sci-wms/sci-wms/issues?state=open](https://github.com/sci-wms/sci-wms/issues?state=open) for a list of known issues and problems.
