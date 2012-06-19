fvcom_wms
=========

*To Start With Django Development Server:

$cd fvcom_wms/src/fvcom_compute

$python manage.py runserver 0.0.0.0:7000

*To Start With Production WSGI Server:

$cd fvcom_wms/src/fvcom_compute

$gunicorn_django -c config.py



For the server to work correctly, you must edit the 
server_local_config.py file. Add the full paths to YOUR
installation of the service, and edit the list of datasets
to include an id and path or opendap link to your dataset.
