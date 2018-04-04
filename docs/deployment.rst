Deployment
==========

Docker (RECOMMENDED)
~~~~~~~~~~~~~~~~~~~~

``sci-wms`` supports running inside of a Docker container

Pull

.. code-block:: bash

    docker pull axiom/sci-wms

Run, interactively

.. code-block:: bash

    docker run --rm -it -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ axiom/sci-wms

Run, daemonized

.. code-block:: bash

    docker run -d -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ axiom/sci-wms

``sci-wms`` will be running on http://localhost:7002.  Adjust the `-p` value to your liking.

Custom Paths
............

Run, with a custom Django config (see ``Custom Django Settings``)

.. code-block:: bash

    docker run -d -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ -v /path/to/settings/folder/containing/settings.py/:/srv/sci-wms/sciwms/settings/local axiom/sci-wms

Run, with a custom topology path (where dataset grids are cached. Useful if load balancing many sci-wms servers together)

.. code-block:: bash

    docker run -d -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ -v /path/to/toplogy/folder:/srv/sci-wms/wms/topology axiom/sci-wms

Superuser
.........

On first run, this image will create a superuser account that can be used to access the ``sci-wms`` admin area, and echo it to the screen, like so:

.. code-block:: bash

    ========================================================================
    sci-wms user:         "sciwmsuser"
    sci-wms user email:   "sciwmsuser@localhost"
    sci-wms password:     "6DZDoN8jmntgj2RY"
    ========================================================================

The default username and email are as shown, and the password is randomly set.  You can manually set all of these by with the environment variables `SCIWMS_USERNAME`, `SCIWMS_EMAIL`, and `SCIWMS_PASSWORD` via the `docker -e` parameter.

For example

.. code-block:: bash

    docker run -d -e SCIWMS_USERNAME=daf -e SCIWMS_PASSWORD=hunter2 axiom/sci-wms


Quick Start (DEVELOPMENT ONLY)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To start ``sci-wms`` with the Django development server on port :7000, type the following commands

.. code-block:: bash

    $ docker run -d --name sciwms-redis -p 6060:6379 redis
    $ python manage.py runserver 0.0.0.0:7002
    $ celery worker -A sciwms
    $ celery beat -A sciwms

This server is not considered secure for production implementations,
and it is recommended you use an alternative wsgi server like *Gunicorn*.


From Source (NOT RECOMMENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You really should be using the Docker image to run ``sci-wms``. This ``From Source`` method won't be supported forever!

You must have a redis instance installed and running on localhost. ``sci-wms`` will use databases ``0`` and ``1``. You should look at the Advanced section for instructions on how to supply your own Django configuration options if you want to configure the Redis connection.


Using the Gunicorn Server
.........................

Gunicorn is recommended for production servers

.. code-block:: bash

    $ celery worker -A sciwms
    $ celery beat -A sciwms
    $ gunicorn \
        --access-logfile - \
        --error-logfile - \
        --max-requests 100 \
        --graceful-timeout 300 \
        --keep-alive 5 \
        --backlog 50 \
        --log-level warning \
        -t 300 \
        -b 0.0.0.0:7002 \
        -w 4 \
        -k tornado \
        -e DJANGO_SETTINGS_MODULE=sciwms.settings.prod \
        -n sciwms \
        sciwms.wsgi:application | logger -t gunicorn

`Gunicorn WSGI server configuration <http://gunicorn.org/>`_


Management with Supervisord
...........................

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

    [program:sci-wms-worker]
    command=celery worker -E -c 4 -A sciwms
    directory=/srv/sci-wms
    user=sciwms
    autostart=true
    autorestart=true
    redirect_stderr=true
    stopasgroup=true
    numprocs=1
    environment=DJANGO_SETTINGS_MODULE="sciwms.settings.prod"

    [program:sci-wms-beat]
    command=celery beat -A sciwms
    directory=/srv/sci-wms
    user=sciwms
    autostart=true
    autorestart=true
    redirect_stderr=true
    stopasgroup=true
    numprocs=1
    environment=DJANGO_SETTINGS_MODULE="sciwms.settings.prod"
