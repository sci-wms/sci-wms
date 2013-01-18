sci-wms
=========

####A Python WMS service for geospatial gridded data (Only unstructured FVCOM and ADCIRC grids and structured grids officially supported)

![Global HYCOM as filled contours](https://raw.github.com/acrosby/sci-wms/master/src/pywms/wms/static/example1.png)

##System Requirements

- >= 4GB RAM But it depends directly on the size and extents of the datasets you will be visualizing.
- > 2 CPU (> 4 CPU Better) 
- Python > Version 2.6

##Roadmap

####Version 1:
- Bug free working implementation of the current dev code
- working getcaps
- working getmap
- working getlegendgraphic for non-autoscaling colormap styles
- service based dataset initialization and updating in addition to admin
- support for native Adcirc and FVCOM model output meshes

####Version 1.1:
- Support for rectilinear and curvilinear grids
- some wps functionality
- projections other than web mercator
- working getlegendgraphic response for the autoscaling colormap styles
- server-wide symbolization customization in admin

####Experimental Fork/Branch:
- Leverage hardware/opengl rendering for high overhead styles (facets, arrows...)


###Caveats:

Look at https://github.com/acrosby/sci-wms/issues?state=open for a list of known issues and problems.

