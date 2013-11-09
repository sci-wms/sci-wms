'''
COPYRIGHT 2010 RPS ASA

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

import fvcom_compute.server_local_config as config

response = '''<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>OpenLayers Image Layer Example</title>
    <link rel="stylesheet" href="http://openlayers.org/dev/theme/default/style.css" type="text/css">
    <link rel="stylesheet" href="http://openlayers.org/dev/examples/style.css" type="text/css">

    <style type="text/css">
        p.caption {
            width: 512px;
        }
    </style>
    <script src="../lib/Firebug/firebug.js"></script>
    <script src="http://openlayers.org/dev/OpenLayers.js"></script>
    <script type="text/javascript">
        var map;
        function init(){
            var options = {numZoomLevels: 100,
                           };
                           
            map = new OpenLayers.Map('map', {
                    
                    
                });

            

            layer = new OpenLayers.Layer.WMS( "OpenLayers WMS",
                    "http://vmap0.tiles.osgeo.org/wms/vmap0", {layers: 'basic'} );
            
            
    
            var jpl_wms = new OpenLayers.Layer.WMS(
                "Alex's FVCOM Facets",
                "http://''' + config.localhostip + '''/wms/", 
                {LAYERS: "facets,average",
                    HEIGHT: "500",
                    WIDTH: "1000",
                    ELEVATION: "1",
                    TIME: "1984-10-17T00:00:00",
                    FORMAT: "image%2Fpng"
                },
                {isBaseLayer: false,
                singleTile: true}
                );
                
            var vec_wms = new OpenLayers.Layer.WMS(
                "Alex's FVCOM Vectors",
                "http://''' + config.localhostip + '''/wms/", 
                {LAYERS: "vectors,maximum",
                    HEIGHT: "500",
                    WIDTH: "1000",
                    ELEVATION: "1",
                    TIME: "1984-10-17T00:00:00",
                    FORMAT: "image%2Fpng"
                },
                {isBaseLayer: false,
                singleTile: true}
                );
 
            map.addLayers([layer, jpl_wms, vec_wms]);
            map.addControl(new OpenLayers.Control.LayerSwitcher());
            map.setCenter(new OpenLayers.LonLat(-70, 42), 5);
        }
    </script>
  </head>
  <body onload="init()">
    <h1 id="title">FVCOM WMS TEST</h1>

    <div id="tags">
        image, imagelayer
    </div>

    <p id="shortdesc">
        Demonstrate a single non-tiled image as a selectable base layer.
    </p>

    <div id="map" class="smallmap"></div>

    <div id="docs">

        <p class="caption">
            FVCOM TEST
        </p>
    </div>
  </body>
</html>
'''
