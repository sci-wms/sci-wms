Deployment
==========

Quickstart
~~~~~~~~~~

If you are working with a moderatly size sci-wms installation (tens of datasets) with light load
you should be ok running a single instance.

.. code-block:: bash

    $ docker run -d axiom/sci-wms


Advanced
~~~~~~~~

If for whatever reason you need to disttibute `sci-wms` instances over many servers it will require a bit more work:

* `redis` for caching and communication between components
* `postgresql` for metadata storage (not SQLite)
* Background workers to perform tasks such as updating datasets
* Shared filesystem for the topology cache

Luckily some really nice person put together an example `docker-compose.yml` file that does it all for you (but on a single server):
https://github.com/sci-wms/sci-wms/blob/background_jobs/docker-compose.yml. If you are at the point of needing to cluster `sci-wms`
then this should help you get started.

.. code-block:: bash

    $ docker-compose up -d

You should see four docker containers:

.. code-block:: bash

    $ docker ps

    CONTAINER ID    IMAGE           COMMAND                  PORTS                    NAMES
    cdc0655e12f2    sci-wms         "/tini -- docker/wai…"   0.0.0.0:7002->7002/tcp   sciwms_web_1
    b2493a0ce881    sci-wms         "/tini -- docker/wai…"   7002/tcp                 sciwms_worker_1
    ee991f4eafbf    postgres:10.3   "docker-entrypoint.s…"   5432/tcp                 sciwms_db_1
    cfa1bf74e03c    redis           "docker-entrypoint.s…"   6379/tcp                 sciwms_redis_1

You can scale out the `worker` nodes as needed:

.. code-block:: bash

    $ docker-compose up -d --scale worker=4 worker

    sciwms_redis_1 is up-to-date
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


Custom Paths
............

To run with a custom Django config, see :ref:`custom-django-settings`, edit the `docker-compose.yml` file
and add a volume to the `web` and `worker` services that mount your custom config file at `/srv/sci-wms/sciwms/settings/local_settings.py`

.. code-block:: bash

    web:
      ...
      volumes:
        - your/settings/file:/srv/sci-wms/sciwms/settings/local_settings.py
      ...

    worker:
      ...
      volumes:
        - your/settings/file:/srv/sci-wms/sciwms/settings/local_settings.py
      ...

To run with a custom Topology Cache path, see :ref:`topology-cache`, edit the `docker-compose.yml` file and add a volume to the `web` and `worker` services. This folder must be shared by all instances of the `worker` and `web`.

.. code-block:: bash

    web:
      ...
      volumes:
        - your/topology/directory:/srv/sci-wms/wms/topology
      ...

    worker:
      ...
      volumes:
          - your/topology/directory:/srv/sci-wms/wms/topology
      ...


Superuser
.........

On first run, this image will create a superuser account that can be used to access the ``sci-wms`` admin area. You can set the user and password by editing the `docker-compose.yml` file and editing the environment variables:

.. code-block:: bash

  web:
    ...
    environment:
      SCIWMS_USERNAME: sciwms
      SCIWMS_PASSWORD: sciwms
    ...

To retrieve the username and password you can view the logs for the `web` service:

.. code-block:: bash

  $ docker logs sciwms_web_1

    ...
    ===============================
    sci-wms user:         "sciwms"
    sci-wms password:     "sciwms"
    ===============================
    ...


Developers
~~~~~~~~~~

To start ``sci-wms`` with the Django development server on port :7002, type the following commands

.. code-block:: bash

    $ python manage.py runserver 0.0.0.0:7002

This server is not considered secure for production implementations, and it is recommended you use
an alternative wsgi server like *Gunicorn*.
