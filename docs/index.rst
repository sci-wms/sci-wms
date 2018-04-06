Welcome to sci-wms
===================================

``sci-wms`` is an open-source Python implementation of a WMS (Web Mapping Service) server designed for oceanographic, atmospheric, climate and weather data.  It achieves real-time, on-demand visualization of internal (file access) and externally hosted (DAP) CF-compliant data.

.. toctree::
   :maxdepth: 2

   deployment
   advanced
   roadmap
   changelog
   support


==========
Background
==========

* No tools for comparing multiple unstructured models out of the box
* Existing WMS technologies (ncWMS and GeoServer) don't support unstructured meshes in a format the preserves topology
* Vast amount of large collections of met-ocean data available over OpenDAP


========
Features
========

- Visualize grids adhering to `CF-UGRID <https://github.com/ugrid-conventions/ugrid-conventions>`_ or `CF-SGRID <https://github.com/sgrid/sgrid>`_ conventions
- Abstracts each dataset into two objects: a topology and corresponding model data
- Topologies are stored locally for quick and efficient spatial queries (RTree indexes for each grid)
- External data (over DAP) is subset, downloaded, and rendered for each request
- Supports arbitrary cartographic projections
- Web-based management console for managing datasets and variables
- Lightweight client for testing


=========
Authors
=========
.. codeauthor:: Alex Crosby <https://github.com/acrosby>
.. codeauthor:: Andrew Yan <https://github.com/ayan-usgs>
.. codeauthor:: Brandon Mayer <https://github.com/brandonmayer>
.. codeauthor:: Brian McKenna <https://github.com/brianmckenna>
.. codeauthor:: Dave Foster <https://github.com/daf>
.. codeauthor:: Kyle Wilcox <https://github.com/kwilcox>
