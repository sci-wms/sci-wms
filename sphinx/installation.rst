Installation
============

===================
System Requirements
===================

* >= 4GB RAM But it depends directly on the size and extents of the datasets you will be visualizing.
* > 2 CPU (> 4 CPU Better)
* Python 2.7.x with sqlite
* LibGeos (http://download.osgeo.org/geos/)
* LibSpatialIndex (http://libspatialindex.github.com)
* netCDF4 C library (with opendap enabled, if opendap/remote functionality is desired)
* libhdf5 C library (dependency of netCDF4)
* libcurl (required for opendap)
* libfreetype
* libpng
* libevent
* libjpeg


========
Download
========

`Download the compressed project and unpack anywhere. <https://github.com/sci-wms/sci-wms>`_ This is where the installation will live.


=======
Install
=======

Install Python dependencies using pip

.. code-block:: bash

    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -r requirements-prod.txt

*if NetCDF4 and HDF5 libraries are in non-typical locations, pass the locations to pip*

.. code-block:: bash

    NETCDF4_DIR=... HDF5_DIR=... pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -r requirements-prod.txt

If you would like Gunicorn to use an alternative worker, the following are also supported:

* eventlet
* tornado


===============
Create Database
===============

.. code-block:: bash


    export DJANGO_SETTINGS_MODULE="sciwms.settings.prod"
    python manage.py migrate
    python manage.py createsuperuser  # prompts to create superuser account


=============
Run the Tests
=============

Install the testing dependencies

.. code-block:: bash

    pip install -r requirements-test.txt

Test that ``sci-wms`` is fully functional by running the following command

.. code-block:: bash

    py.test -rxs --verbose


========
Updating
========

From version 1.0.0 ``sci-wms`` is easily upgraded to a newer version:

1. Stop any running instances of ``sci-wms``
2. Replace your current ``sci-wms`` directory with the new version (using git pull)
3. Migrate the database: ``DJANGO_SETTINGS_MODULE="sciwms.settings.prod" python manage.py migrate``
4. Start ``sci-wms`` as you usually would
