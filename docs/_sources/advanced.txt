Advanced Usage
==============


Docker
~~~~~~

``sci-wms`` supports running inside of a Docker container

Pull

.. code-block:: bash

    docker pull axiom/sci-wms

Run, interactively

.. code-block:: bash

    docker run --rm -it -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ sci-wms

Run, daemonized

.. code-block:: bash

    docker run -d -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ sci-wms

``sci-wms`` will be running on http://localhost:7002.  Adjust the `-p` value to your liking.

Custom Paths
............

Run, with a custom Django config (see ``Custom Django Settings``)

.. code-block:: bash

    docker run -d -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ -v /path/to/settings/folder/containing/settings.py/:/srv/sci-wms/sciwms/settings/local sci-wms

Run, with a custom topology path (where dataset grids are cached. Useful if load balancing many sci-wms servers together)

.. code-block:: bash

    docker run -d -p 7002:7002 -v /your/local/folder/for/sqlite/database:/srv/sci-wms/sciwms/db/ -v /path/to/toplogy/folder:/srv/sci-wms/wms/topology sci-wms

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

    docker run -d -e SCIWMS_USERNAME=daf -e SCIWMS_PASSWORD=hunter2 sci-wms


Virtual layers
~~~~~~~~~~~~~~

**Virtual Layers** allow you to use a parameter expression to access multiple variables from a dataset in a special way, while specifying a descriptive layer name that will also appear in the *GetCapabilities* documents. This is so that generic web clients don't necessarility need to know the intracacies of assembling ``sci-wms`` parameter expressions in requests.

Suported parameter expressions:

``[layer_1],[layer_2]`` This will treat layer_1 as a U vector and layer_2 as a V vector and produce vector plots.


Custom Django Settings
~~~~~~~~~~~~~~~~~~~~~~

You may create a file at **path/to/sci-wms/sci-wms/settings/local_settings.py** or **path/to/sci-wms/sci-wms/settings/local/settings.py** and configure any Django settings you wish.  The latter takes presedence over the former.

The following settings are recommended:

.. code-block:: python

    # Specific host(s) that that server should be accessible on
    ALLOWED_HOSTS  = ["sciwms.external-host.com", "YOUR_IP_ADDRESS", "sciwms.internal-host"]


.. code-block:: python

    # Sci-wms caches data on disk so it does not have to read static data from each dataset every request.
    # By default, the path is `SCIWMS_ROOT/sciwms/apps/wms/topology`.
    TOPOLOGY_PATH = "/data/sci-wms-topology"
    if not os.path.exists(TOPOLOGY_PATH):
        os.makedirs(TOPOLOGY_PATH)


Topology Cache
~~~~~~~~~~~~~~

The topology cache is an important optimization that speeds up response times for datasets that are accessed over opendap. The cache is current located in the folder of the ``sci-wms`` instance at ``path/to/sci-wms/wms/topology``. There are a number of files that make up the cache, and they vary by dataset type.

Each file has a name that is taken directly from the ``sci-wms`` **Dataset**'s **'Name'**.


Spatial Tree (.idx and .dat)
............................

These files contain serialized *RTree* spatial objects that are used for quickly making nearest neighbor queries as part of GetFeatureInfo requests.

These are necessary for large unstructured meshes, but are also used for the logically rectangular grids as well.  Ideally it would be nice to move away from *RTree* into a better KD-Tree implementation, like *sklearn*'s, that will have better on disk performance lookup performance, but will be slower to initially build.

These files are constructed once when the dataset is added and never updated.  If the grid for you model changes you must delete and re-add the model to regenerate the topology cache.

Adding a dataset via the website may timeout due to the topology cache taking along time to complete. If you run across this case, it is better to add the Dataset manually through the Django shell.


NetCDF (.nc)
............

This file contains the up-to-date coordinate variable data for the dataset. This is typically Latitude/Longitude, and Time. For forecasts that are routinely updates, the time variable typically is growing with each update.  This file is updated if the Dataset is set to "Keep up to date" and an update is requested.



Default Layer Settings
~~~~~~~~~~~~~~~~~~~~~~

``sci-wms`` takes a three tier approach to figure out what the ``min``, ``max``, and ``logscale`` values should be for a request.

In order of precedence:

1. URL request arguments
    Always preferred for maximum client control. Controlled with the ``LOGSCALE`` and ``COLORSCALERANGE`` URL parameters.

2. Layer defaults
    Used when populated on a ``Layer`` not specified in the URL request. Controlled on each dataset page on a per-variable basis.

3. Global defaults
    Used when the previous two are not populated. Controlled on the global defaults page on a ``standard_name`` and ``units`` basis.



WMS Extensions
~~~~~~~~~~~~~~

``sci-wms`` implements a number of additional WMS parameters that are not defined in the WMS specification while remaining completely backwards compatible.

.. csv-table:: WMS Extensions
   :header: "Parameter", "Requests", "Possible Values", "Usage", "Examples"
   :widths: 10, 20, 20, 70, 20

   "LOGSCALE", "GetLegendGraphic GetMap", "``true``, ``false``", "If the request should use logscaling", "``true`` ``false``"
   "COLORSCALERANGE", "GetLegendGraphic GetMap", "``[min],[max]``", "A tuple in the format [min],[max] that defines the scale range to visualize", "``1,100``  ``4.5,30``"
   "SHOWLABEL", "GetLegendGraphic", "``true``, ``false``", "If the units label should be shows in the legend", "``true`` ``false``"
   "SHOWVALUES", "GetLegendGraphic", "``true``, ``false``", "If the value ticks should be shows in the legend", "``true`` ``false``"
   "UNITLABEL", "GetLegendGraphic", "``[text]``", "Set the unit label on a legend to a custom value", "``meters`` ``degC``"
   "HORIZONTAL", "GetLegendGraphic", "``true``, ``false``", "Return a horizontal legend (vertical is the default)", "``true`` ``false``"
   "NUMCONTOURS", "GetLegendGraphic GetMap", "``[int]``", "Return request with the specified number of contours. Only valid for the ``image_type`` of ``contours`` or ``filledcontours``).", "``8``  ``30``"
   "STYLE", "GetLegendGraphic GetMap", "``[image_type]``_``[colormap]``", "While some styles are defined in the GetCapabilities document, a use can specify any combination of an ``image_type`` (``filledcontours``, ``contours``, ``pcolor``, ``vectors``, ``filledhatches``, ``hatches``) and a matplotlib ``colormap`` (http://matplotlib.org/examples/color/colormaps_reference.html)", "``contours_jet``  ``vectors_blues``"
   "VECTORSCALE", "GetMap", "``[float]``", "Controls the scale of vector arrows when plotting a ``vectors`` style. The ``vectorscale`` value represents the number of data units per arrow length unit. Smaller numbers lead to longer arrows, while larger numbers represent shorter arrows. This is consistent with the use of the ``scale`` keyword used by matplotlib (http://matplotlib.org/api/pyplot_api.html).", "``10.5`` ``30``"
   "VECTORSTEP", "GetMap", "``[int]``", "Set the number of vector steps to be used when rendering a GetMap request using a ``vectors`` style. A value of ``1`` will render with all vectors and is the default behavior.", "``2`` ``10``"
