Deployment
==========


Getting started
~~~~~~~~~~~~~~~

Deployment of sci-wms is simplified by using Docker. You will need do install `Docker <https://docs.docker.com/install/>`_ and `docker-compose <https://docs.docker.com/compose/install/>`_.

.. _quickstart-run:

Quickstart
~~~~~~~~~~

If you are working with a small ``sci-wms`` installation - a few small datasets and light load - you should ok running with this quickstart setup. The web and background workers need to share the same datasbase files so be sure to mount a database directory into both.

.. code-block:: docker

    $ cat docker-compose.yml

    version: '3.2'

    services:

      web:
        image: axiom/sci-wms
        environment:
          DJANGO_SETTINGS_MODULE: sciwms.settings.quick
        ports:
          - "7002:7002"
        volumes:
          - topologydata:/srv/sci-wms/wms/topology:ro
          - dbdata:/srv/sci-wms/sciwms/db/

      worker:
        image: axiom/sci-wms
        environment:
          DJANGO_SETTINGS_MODULE: sciwms.settings.quick
        volumes:
          - topologydata:/srv/sci-wms/wms/topology
          - dbdata:/srv/sci-wms/sciwms/db/
        command: python manage.py run_huey

    volumes:
      topologydata:
      dbdata:


Run the containers

.. code-block:: bash

  $ docker-compose up -d


You should see *two* docker containers:

.. code-block:: bash

    $ docker ps

    CONTAINER ID    IMAGE           COMMAND                  PORTS                    NAMES
    cdc0655e12f2    sci-wms         "/tini -- docker/wai…"   0.0.0.0:7002->7002/tcp   sciwms_web_1
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_1


.. _advanced-run:

Advanced
~~~~~~~~

If you are working with a moderatly size ``sci-wms`` installation you will need to run background workers to manage adding new datsets and updating existing datasets. This requires `redis <https://redis.io/>`_ to share information between the web and background workers as well as `postgres <https://www.postgresql.org/>`_ so the web and background workers can share the same metadata database.

.. code-block:: bash

    $ cat docker-compose.yml

    version: '3.2'

    services:

      redis:
        image: redis

      db:
        image: postgres:10.3
        environment:
          POSTGRES_USER: sciwms
          POSTGRES_PASSWORD: sciwms
          POSTGRES_DB: sciwms
        volumes:
          - dbdata:/var/lib/postgresql/data

      web:
        image: axiom/sci-wms
        environment:
          DJANGO_SETTINGS_MODULE: sciwms.settings.adv
        ports:
          - "7002:7002"
        depends_on:
          - db
          - redis
        volumes:
          - topologydata:/srv/sci-wms/wms/topology:ro
        command: docker/wait.sh db:5432 -- docker/run.sh

      worker:
        image: axiom/sci-wms
        environment:
          DJANGO_SETTINGS_MODULE: sciwms.settings.adv
        depends_on:
          - db
          - redis
        volumes:
          - topologydata:/srv/sci-wms/wms/topology
        command: docker/wait.sh web:7002 -- python manage.py run_huey

    volumes:
      dbdata:
      topologydata:


Run the containers

.. code-block:: bash

  $ docker-compose up -d


You should see *four* docker containers:

.. code-block:: bash

    $ docker ps

    CONTAINER ID    IMAGE           COMMAND                  PORTS                    NAMES
    cdc0655e12f2    sci-wms         "/tini -- docker/wai…"   0.0.0.0:7002->7002/tcp   sciwms_web_1
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_1
    ee991f4eafbf    postgres:10.3   "docker-entrypoint.s…"   5432/tcp                 sciwms_db_1
    cfa1bf74e03c    redis           "docker-entrypoint.s…"   6379/tcp                 sciwms_redis_1


You can scale out the ``worker`` nodes as needed:

.. code-block:: bash

    $ docker-compose up -d --scale worker=4 worker

    Starting sciwms_worker_1 ... done
    Starting sciwms_worker_2 ... done
    Starting sciwms_worker_3 ... done
    Starting sciwms_worker_4 ... done

    $ docker ps

    CONTAINER ID    IMAGE           COMMAND                  PORTS                    NAMES
    cdc0655e12f2    sci-wms         "/tini -- docker/wai…"   0.0.0.0:7002->7002/tcp   sciwms_web_1
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_1
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_2
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_3
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_4
    ee991f4eafbf    postgres:10.3   "docker-entrypoint.s…"   5432/tcp                 sciwms_db_1
    cfa1bf74e03c    redis           "docker-entrypoint.s…"   6379/tcp                 sciwms_redis_1


**sci-wms will now be running on port 7002**. To obtain a python shell to test commands and such:

.. code-block:: bash

    $ docker exec -it sciwms_web_1 python


Configuration
~~~~~~~~~~~~~

Web Concurrency
...............

If you find your instance can not serve WMS requests fast enough you can add additional web workers. ``sci-wms`` uses ``eventlet`` on the backend and a single web worker instance should be able to handle hundreds of simultaneous requests. If you are using the default :ref:`quickstart-run`, however, than the Update of each dataset will block a worker until it is done and you can safely add as many as you want. A good default is the number of CPU cores you have or the number
you would like to dedicate to ``sci-wms`` when under heavy load.


Using ``docker``

.. code-block:: bash

  $ docker run -d -e "WEB_CONCURRENCY=8" axiom/sci-wms


Using ``docker-compose``

.. code-block:: bash

  web:
    ...
    environment:
      WEB_CONCURRENCY: 8
    ...


.. _custom-django-settings:

Custom Django Settings
......................

You may create a file at ``/srv/sci-wms/sciwms/settings/local_settings.py`` or ``/srv/sci-wms/ sciwms/settings/local/settings.py`` and configure any Django settings you wish.  The latter takes presedence over the former.

.. code-block:: bash

    web:
      ...
      volumes:
        - your_settings.py:/srv/sci-wms/sciwms/settings/local_settings.py:ro
      ...

    worker:
      ...
      volumes:
        - your_settings.py:/srv/sci-wms/sciwms/settings/local_settings.py:ro
      ...


The following settings are recommended:

.. code-block:: python

    # Specific host(s) that that server should be accessible on
    ALLOWED_HOSTS  = ["sciwms.external-host.com", "YOUR_IP_ADDRESS", "sciwms.internal-host"]


Topology Cache
..............

To run with a custom Topology Cache path, see :ref:`topology-cache`, edit the ``docker-compose.yml`` file and add a volume to the ``web`` and ``worker`` services. This folder must be shared by all instances of the ``worker`` and ``web`` but only the ``worker`` instances need to write to it.

.. code-block:: bash

    web:
      ...
      volumes:
        - your/topology/directory:/srv/sci-wms/wms/topology:ro
      ...

    worker:
      ...
      volumes:
          - your/topology/directory:/srv/sci-wms/wms/topology
      ...


Superuser
.........

On first run, this image will create a superuser account that can be used to access the ``sci-wms`` admin area. You can set the user and password by editing the ``docker-compose.yml`` file and editing the environment variables:

.. code-block:: bash

  web:
    ...
    environment:
      SCIWMS_USERNAME: sciwms
      SCIWMS_PASSWORD: sciwms
    ...

To retrieve the username and password you can view the logs for the ``web`` service:

.. code-block:: bash

  $ docker logs sciwms_web_1

    ...
    ===============================
    sci-wms user:         "sciwms"
    sci-wms password:     "sciwms"
    ===============================
    ...


Secret Key
..........

You will need to set the ``DJANGO_SECRET_KEY`` environmental variable on any web worker containers. Set it to your favorite quote or a long random string

Using ``docker``

.. code-block:: bash

  $ docker run -d -e "DJANGO_SECRET_KEY=thewaytogetstartedistoquittalkingandbegindoing" axiom/sci-wms


Using ``docker-compose``

.. code-block:: bash

  web:
    ...
    environment:
      DJANGO_SECRET_KEY: thewaytogetstartedistoquittalkingandbegindoing
    ...
