Deployment
==========


==============================
Quick Start (DEVELOPMENT ONLY)
==============================

To start ``sci-wms`` with the Django development server on port :7000, type the following commands

.. code-block:: bash

    python manage.py runserver 0.0.0.0:7002

This server is not considered secure for production implementations,
and it is recommended you use an alternative wsgi server like *Gunicorn*.

=========================
Using the Gunicorn Server
=========================

Gunicorn is recommended for production servers

start services on port 7002 (port specified in `gunicorn_config_prod.py`)

.. code-block:: bash

    gunicorn -c gunicorn_config_prod.py sciwms.wsgi:application

`Gunicorn WSGI server configuration <http://gunicorn.org/>`_


===========================
Management with Supervisord
===========================

Sample supervisord configuration for ``sci-wms`` assuming installation at ``/srv/sci-wms``
and running as the ``sciwms`` user.  You should specify the full path to the ``gunicorn`` executable
you want to use (the one installed inside of your virtualenv).

.. code-block:: bash

    [program:sci-wms]
    command=gunicorn -w 8 -t 300 -b 127.0.0.1:7002 -n sciwms --max-requests 100 --access-logfile /srv/sci-wms/logs/gunicorn.access.log --error-logfile /srv/sci-wms/logs/gunicorn.error.log -k tornado sciwms.wsgi:application
    directory=/srv/sci-wms
    user=sciwms
    autostart=true
    autorestart=true
    redirect_stderr=true
    stopasgroup=true
    numprocs=1
    environment=DJANGO_SETTINGS_MODULE="sciwms.settings.prod"
