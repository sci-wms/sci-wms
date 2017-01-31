Installation
============

System Requirements
~~~~~~~~~~~~~~~~~~~

* >= 4GB RAM But it depends directly on the size and extents of the datasets you will be visualizing.
* > 2 CPU (> 4 CPU Better)


Docker
~~~~~~

`docker pull axiom/sci-wms`


Source
~~~~~~

`Download the compressed project and unpack anywhere. <https://github.com/sci-wms/sci-wms>`_ This is where the installation will live.

Install Dependencies 
....................

If you need the `conda` executable command, see `this <http://conda.pydata.org/miniconda.html>`_.

.. code-block:: bash

    conda install -c axiom-data-science -c ioos  --file requirements.txt
    conda install -c axiom-data-science -c ioos  --file requirements-dev.txt
    conda install -c axiom-data-science -c ioos  --file requirements-prod.txt


Create Database
...............

.. code-block:: bash

    export DJANGO_SETTINGS_MODULE="sciwms.settings.prod"
    python manage.py migrate
    python manage.py collectstatic


Run the Tests
.............

Install the testing dependencies

.. code-block:: bash

    conda install -c axiom-data-science -c ioos  --file requirements-test.txt

Test that ``sci-wms`` is fully functional by running the following command

.. code-block:: bash

    py.test -s -rxs -v
