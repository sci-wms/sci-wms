=========
Changelog
=========

* :release:`1.5.0 <2015-12-18>`
* :feature:`106` Add the UTIDES dataset type
* :bug:`105 major` Changed default size of Legend to match ncWMS
* :release:`1.4.0 <2015-11-19>`
* :feature:`106` Support the ``COLORBARONLY`` parameter in GetLegendGraphic
* :feature:`101` Ability to view sci-wms logs from the web client (login only)
* :bug:`105 major` Allow empty width/height parameters in GetLegendGraphic requests
* :bug:`107 major` Fix lat/lon order on UGRID datasets
* :release:`1.3.0 <2015-11-02>`
* :feature:`95` Release sci-wms on Dockerhub
* :feature:`97` Added default_style and default_numcontours to Layer
* :feature:`94` Updated RTree library
* :feature:`93` Python 3.4 support
* :feature:`92` Added hatching styles
* :feature:`86` Implement the ``pcolor`` image type for UGRID
* :feature:`91` Implement ``LOGSCALE`` on GetMap requests
* :feature:`90` Set ``cubehelix`` as the default colormap
* :release:`1.2.0 <2015-10-28>`
* :feature:`-` Support Django>=1.7 (including 1.8)
* :feature:`-` Upgrade to ``django-typed-models`` 0.5.0
* :feature:`89` Add ``contours`` support to GetMap
* :feature:`88` Add ``NUMCONTOURS`` support to GetMap :doc:`/advanced`
* :release:`1.0.0 <2015-07-08>`
* :feature:`18` Much improved documentation :doc:`/advanced`
* :feature:`4` Much improved documentation :doc:`/roadmap`
* :feature:`8` Much improved documentation :doc:`/deployment`
* :feature:`35` Support CF-SGRID datasets via ``pyugrid``
* :feature:`-` Support CF-UGRID datasets via ``pysgrid``
* :feature:`36` Support for running in a Docker container
* :feature:`32` Integration of COMT branch
* :feature:`7` Upgrade to Django 1.7
* :feature:`45` Support datasets with more than one ``standard_name: time``
* :feature:`-` Ability to set min/max limits in web interface
