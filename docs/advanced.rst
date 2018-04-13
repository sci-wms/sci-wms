Advanced Topics
===============


Virtual layers
~~~~~~~~~~~~~~

**Virtual Layers** allow you to use a parameter expression to access multiple variables from a dataset in a special way, while specifying a descriptive layer name that will also appear in the *GetCapabilities* documents. This is so that generic web clients don't necessarility need to know the intracacies of assembling ``sci-wms`` parameter expressions in requests.

Suported parameter expressions:

``[layer_1],[layer_2]`` This will treat layer_1 as a U vector and layer_2 as a V vector and produce vector plots.


.. _topology-cache:

Topology Cache
~~~~~~~~~~~~~~

The topology cache is an important optimization that speeds up response times for datasets that are accessed over opendap. The cache is current located in the folder of the ``sci-wms`` instance at ``path/to/sci-wms/wms/topology``. There are a number of files that make up the cache, and they vary by dataset type.

Each file has a name that is taken directly from the ``sci-wms`` **Dataset**'s **'Name'**.


Spatial Tree (.idx and .dat)
............................

These files contain serialized *RTree* spatial objects that are used for quickly making nearest neighbor queries as part of GetFeatureInfo requests.

These are necessary for large unstructured meshes, but are also used for the logically rectangular grids as well.  Ideally it would be nice to move away from *RTree* into a better KD-Tree implementation, like *sklearn*'s, that will have better on disk performance lookup performance, but will be slower to initially build.

These files are constructed once when the dataset is added and not updated unless an ``Update Dataset`` request is triggered via the ``sci-wms`` admin page or API. If a dataset is set to ``Keep up to date`` then it will update this cache every X seconds, depending on what the dataset is configured for.

Adding a new dataset through the website when running in :ref:`quickstart-run` mode may timeout due to the topology cache taking along time to complete. If you run across this case, it is better to add the Dataset manually through the command line (no documentation at this point) or to use the :ref:`advanced-run` mode of running ``sci-wms``.


NetCDF (.nc)
............

This file contains the up-to-date coordinate variable data for the dataset. This is typically Latitude/Longitude, and Time. For forecasts that are routinely updates, the time variable typically is growing with each update.  This file is updated periodially if the ``Dataset`` is set to "Keep up to date" or an update is manually triggered via the ``sci-wms`` admin page or API.


Default Layer Settings
~~~~~~~~~~~~~~~~~~~~~~

``sci-wms`` takes a three tier approach to figure out what the ``min``, ``max``, and ``logscale`` values should be for a request.

In order of precedence:

1. URL request arguments
    Always preferred for maximum client control. Controlled with the ``LOGSCALE`` and ``COLORSCALERANGE`` URL parameters.

2. Layer defaults
    Used when populated on a ``Layer``. Controlled on each ``Dataset`` page on a per-variable basis. For each netCDF variable, we look for the following when processing a variable in order of most precedence first:

      #. `scale_min` and `scale_max`
      #. `scale_range`
      #. `valid_min` and `valid_max`
      #. `valid_range`

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
   "COLORBARONLY", "GetLegendGraphic", "``true``, ``false``", "If ``true``, effectively sets ``SHOWVALUES`` and ``SHOWLABEL`` to ``false``. This will override the individual setttings of ``SHOWVALUES`` and ``SHOWLABEL``. No effect if this is set to ``false``.", "``true`` ``false``"
   "UNITLABEL", "GetLegendGraphic", "``[text]``", "Set the unit label on a legend to a custom value", "``meters`` ``degC``"
   "HORIZONTAL", "GetLegendGraphic", "``true``, ``false``", "Return a horizontal legend (vertical is the default)", "``true`` ``false``"
   "NUMCONTOURS", "GetLegendGraphic GetMap", "``[int]``", "Return request with the specified number of contours. Only valid for the ``image_type`` of ``contours`` or ``filledcontours``).", "``8``  ``30``"
   "STYLE/STYLES", "GetLegendGraphic GetMap", "``[image_type]_[colormap]``", "While some styles are defined in the GetCapabilities document, a use can specify any combination of an ``image_type`` (``filledcontours``, ``contours``, ``pcolor``, ``vectors``, ``filledhatches``, ``hatches``) and a matplotlib ``colormap`` (http://matplotlib.org/examples/color/colormaps_reference.html)", "``contours_jet``  ``vectors_blues``"
   "VECTORSCALE", "GetMap", "``[float]``", "Controls the scale of vector arrows when plotting a ``vectors`` style. The ``vectorscale`` value represents the number of data units per arrow length unit. Smaller numbers lead to longer arrows, while larger numbers represent shorter arrows. This is consistent with the use of the ``scale`` keyword used by matplotlib (http://matplotlib.org/api/pyplot_api.html).", "``10.5`` ``30``"
   "VECTORSTEP", "GetMap", "``[int]``", "Set the number of vector steps to be used when rendering a GetMap request using a ``vectors`` style. A value of ``1`` will render with all vectors and is the default behavior.", "``2`` ``10``"


Developers
~~~~~~~~~~

To start ``sci-wms`` with the Django development server on port :7002, type the following commands

.. code-block:: bash

    $ python manage.py runserver 0.0.0.0:7002

This server is not considered secure for production implementations, and it is recommended you use
an alternative wsgi server like *Gunicorn*.
