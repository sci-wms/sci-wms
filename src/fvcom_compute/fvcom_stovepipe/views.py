'''
Created on Sep 1, 2011

@author: ACrosby
'''
# Create your views here.
from django.http import HttpResponse
import numpy
import netCDF4
from fvcom_compute.fvcom_stovepipe.models import Cell, Time, Node
from matplotlib import pyplot as Plot
from mpl_toolkits.basemap import Basemap
import datetime
from collections import deque
from StringIO import StringIO
import scipy.io
import math
import pp
import fvcom_compute.server_local_config as config

def wmstest (request):
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
                "http://192.168.100.146:8000/wms/", 
                {LAYERS: "facets,average",
                    HEIGHT: "10",
                    WIDTH: "10",
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
                    HEIGHT: "10",
                    WIDTH: "10",
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
    
    return HttpResponse(response)

def documentation (request):
    import django.shortcuts as dshorts
    #import fvcom_compute.server_local_config as config
    f = open(config.staticspath + "doc.txt")
    text = f.read()
    dict = { "textfile":text}
    return dshorts.render_to_response('docs.html', dict)

def test (request):
    import django.shortcuts as dshorts
    #import fvcom_compute.server_local_config as config
    f = open(config.staticspath + "test.txt")
    text = f.read()
    dict = { "textfile":text}
    return dshorts.render_to_response('docs.html', dict)

def wms (request):
    import fvcom_compute.fvcom_stovepipe.wms_handler as wms
    handler = wms.wms_handler(request)
    action_request = handler.make_action_request(request)
    response = fvDo(action_request)
    return response

def populate (request):
    
    from netCDF4 import Dataset, num2date
    url = config.datasetpath
    nc = Dataset(url)
    lat = nc.variables['lat'][:]
    lon = nc.variables['lon'][:]
    latc = nc.variables['latc'][:]
    lonc = nc.variables['lonc'][:]
    nv = nc.variables['nv'][:,:]
    times = nc.variables['time']
    time = num2date(times[:], units=times.units)

    nodes = Node.objects.all()
    nodes.delete()
    cells = Cell.objects.all()
    cells.delete()
    times = Time.objects.all()
    times.delete()
    for i,d in enumerate(time):
        #d = datetime.datetime(int(time[i][0]), int(time[i][1]), int(time[i][2]),\
        #    int(time[i][3]), int(time[i][4]), int(time[i][5]))
        t = Time(date=d, index=i+1)
        t.save()
    
    for i in range(len(lat)):
        n = Node(index=i+1, lat=lat[i], lon=lon[i])
        n.save()
        
    for i in range(len(latc)):
        c = Cell(index=i+1, lat=latc[i], lon=lonc[i], node1=nv[0, i], node2=nv[1, i], node3=nv[2, i])
        c.save()
        
    return "done!"


def fvDo (request):
    '''
    Request a set of functionalities, any subset of the following:
    1) WMS Style Image Request
    2) WMS Style Image Request for Vectors
    3) Regridding
    4) Request t/lat/lon/z chunk
    5) Do averaging
    With appropriate parameters for each (parameters my overlap).
    '''
    
    def getVals(queryset, value):
        if value == 1:
            out = queryset["index"]
            out = int(out)-1
        elif value == 2:
            out = queryset["lat"]
        elif value == 3:
            out = queryset["lon"]
        elif value == 4:
            out = queryset["date"]
            #out = int(out)-1
        elif value ==5:
            out = queryset["node1"]
            out = int(out)-1
        elif value ==6:
            out = queryset["node2"]
            out = int(out)-1
        elif value ==7:
            out = queryset["node3"]
            out = int(out)-1
        return out
    
    def haversine(lat1, lon1, lat2, lon2):
        # Haversine formulation
        # inputs in degrees
        startX = math.radians(lon1)
        startY = math.radians(lat1)
        endX = math.radians(lon2)
        endY = math.radians(lat2)
        diffX = endX - startX
        diffY = endY - startY
        a = math.sin(diffY/2)**2 + math.cos(startY) * math.cos(endY) * math.sin(diffX/2)**2
        c = 2 * math.atan2(math.sqrt(a),  math.sqrt(1-a))
        length = 6371 * c
        return length
    
    def reorderArray(values, numsrow, numscol):
        grid = [];
        for i in range(numsrow):
            grid.append(values[ (i * numscol):((i * numscol) + (numscol - 1)) ])
        return grid
    
    # direct the service to the dataset      
    if config.localdataset:
        url = config.localpath
    else:
        url = config.datasetpath
        
    
    width = int(request.GET["width"])
    height = int(request.GET["height"])
    latmax = float(request.GET["latmax"])
    latmin = float(request.GET["latmin"])
    lonmax = float(request.GET["lonmax"])
    lonmin = float(request.GET["lonmin"])
    datestart = request.GET["datestart"]
    dateend = request.GET["dateend"]
    layer = request.GET["layer"]
    layer = layer.split(",")
    for i,l in enumerate(layer):
        layer[i] = int(l)-1
    layer = numpy.asarray(layer)
    actions = request.GET["actions"]
    actions = set(actions.split(","))
    #if latmax == latmin:
    #    actions.append("timeseries")
    if "kml" in actions:
        actions.discard("kml")
        where = request.get_full_path()
        where = where.replace("kml,", "")
        where = where.replace("kml", "")
        where = where.replace("&", "&amp;")
        kml = ('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Folder>
    <name>fvcom overlays</name>
    <description>Requested plot of fvcom data</description>
    <GroundOverlay>
      <name>FVCOM</name>
      <description>Display of processed fvcom data from requested kml.</description>
      <Icon>
        <href>http://localhost:8000''' + where + '''</href>
      </Icon>
      <LatLonBox>
        <north>''' + str(latmax) + '''</north>
        <south>''' + str(latmin) + '''</south>
        <east>''' + str(lonmax) + '''</east>
        <west>''' + str(lonmin) + '''</west>
        
      </LatLonBox>
    </GroundOverlay>
  </Folder>
</kml>
        ''')
        
        response = HttpResponse(content_type="application/vnd.google-earth.kml+xml")
        response['Content-Disposition'] = 'filename=fvcom.kml'
        response.write(kml)
    else:
        if latmax != latmin:
            geobb = Cell.objects.filter(lat__lte=latmax).filter(lat__gte=latmin)\
                .filter(lon__lte=lonmax).filter(lon__gte=lonmin)
            indexqs = geobb.values("index")
            latqs = geobb.values("lat")
            lonqs = geobb.values("lon")
            
            index = map(getVals, indexqs, numpy.ones(len(indexqs)))
            lat = map(getVals, latqs, numpy.ones(len(indexqs))*2)
            lon = map(getVals, lonqs, numpy.ones(len(indexqs))*3)
        else:
            geobb = Cell.objects.filter(lat__lte=latmax+.1).filter(lat__gte=latmin-.1)\
                .filter(lon__lte=lonmax+.1).filter(lon__gte=lonmin-.1)
            indexqs = geobb.values("index")
            latqs = geobb.values("lat")
            lonqs = geobb.values("lon")
            index = map(getVals, indexqs, numpy.ones(len(indexqs))*1)
            lat = map(getVals, latqs, numpy.ones(len(indexqs))*2)
            lon = map(getVals, lonqs, numpy.ones(len(indexqs))*3)
            lengths = map(haversine, numpy.ones(len(lon))*latmax, \
                          numpy.ones(len(lon))*lonmax, lat, lon)
            min = numpy.asarray(lengths)
            min = numpy.min(min)
            ind = lengths.index(min)
            lat = lat[ind]
            lon = lon[ind]
            index = index[ind]
        
        if ("facets" in actions) or \
        ("regrid" in actions) or \
        ("shp" in actions):
            from matplotlib.collections import PolyCollection
            import matplotlib.tri as Tri
            node1qs = geobb.values("node1")
            node2qs = geobb.values("node2")
            node3qs = geobb.values("node3")
            nodesqs = Node.objects.all().values()
            latnqs = nodesqs.values("lat")
            lonnqs = nodesqs.values("lon")
            latn = map(getVals, latnqs, numpy.ones(len(latnqs))*2)
            lonn = map(getVals, lonnqs, numpy.ones(len(latnqs))*3)
            latn = numpy.asarray(latn)
            lonn = numpy.asarray(lonn) 
            node1 = map(getVals, node1qs, numpy.ones(len(indexqs))*5)
            node2 = map(getVals, node2qs, numpy.ones(len(indexqs))*6)
            node3 = map(getVals, node3qs, numpy.ones(len(indexqs))*7)
            nv = numpy.asarray([node1, node2, node3],'int64')
            nv = numpy.transpose(nv)
            #if "facets" in actions:
                #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                #                   urcrnrlon=lonmax, urcrnrlat=latmax,
                #                    projection='tmerc', lat_0 =(latmax + latmin) / 2,
                #                     lon_0 =(lonmax + lonmin) / 2)
                #lonn, latn = m(lonn, latn)
            #tri = Tri.Triangulation(lonn,latn,triangles=nv)
            
        #for i, p in enumerate(indexqs): # remove 1:5 for full scale test, too slow?
        #    index.append(int(p["index"]) - 1)
        #    lat.append(latqs[i]["lat"])
        #    lon.append(lonqs[i]["lon"])
        #index = [i["index"] for i in indexqs] # too slow?
        #lat = [i["lat"] for i in latqs]
        #lon = [i["lon"] for i in lonqs]
        
        #if date = 
        datestart = datetime.datetime.strptime( datestart, "%Y-%m-%dT%H:%M:%S" )
        dateend = datetime.datetime.strptime( dateend, "%Y-%m-%dT%H:%M:%S" )
        timesqs = Time.objects.filter(date__gte=datestart).filter(date__lte=dateend).values("index")
        #time = map(getVals, timesqs, numpy.ones(len(timesqs))*1) # commented out for testing of local speed
        time = range(50)
        pv = deque()
        pu = deque()
        def getuvar(url, t, layer):
            nc = netCDF4.Dataset(url)
            return nc.variables["u"][t, layer[0], :]
        def getvvar(url, t, layer):
            nc = netCDF4.Dataset(url)
            return nc.variables["v"][t, layer[0], :]
        appendu = pu.append
        appendv = pv.append
        job_server = pp.Server(16, ppservers=())
        

        # This is looping through time to avoid trying to download too much data from the server at once
        # and its SO SLOOOW, i think due to the append calls, maybe use np.concatenate>?
        for t in time:
            appendu(job_server.submit(getuvar, (url, t, layer),(), ("netCDF4", "numpy",))) 
            appendv(job_server.submit(getvvar, (url, t, layer),(), ("netCDF4", "numpy",)))
        
        u = deque()
        v = deque()
        
        [v.append(resultv()) for resultv in pv]
        [u.append(resultu()) for resultu in pu]
        v = numpy.asarray(v)
        u = numpy.asarray(u)
        index = numpy.asarray(index)
        if len(v.shape) > 2:
            v = v[:, :, index]
            u = u[:, :, index]
        elif len(v.shape) > 1:
            v = v[:, index]
            u = u[:, index]
        else: pass # or 1 timestep geographic...?...

        if latmin != latmax:
            # This is averaging in time over all timesteps downloaded
            if not "animate" in actions:
                if "average" in actions:
                    if len(v.shape) > 2:
                        v = v.mean(axis=0)
                        u = u.mean(axis=0)
                        v = v.mean(axis=0)
                        u = u.mean(axis=0)
                    elif len(v.shape) > 1:
                        v = v.mean(axis=0)
                        u = u.mean(axis=0)
                if "maximum" in actions:
                    if len(v.shape) > 2:
                        v = v.max(axis=0)
                        u = u.max(axis=0)
                        v = v.max(axis=0)
                        u = u.max(axis=0)
                    elif len(v.shape) > 1:
                        v = v.max(axis=0)
                        u = u.max(axis=0)
            else: pass # will eventually add animations over time, instead of averages

            if "image" in actions:
                fig = Plot.figure(dpi=150, facecolor='none', edgecolor='none')
                fig.set_alpha(0)
                #ax = fig.add_subplot(111)
                projection = request.GET["projection"]
                m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                            #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                            lat_ts = 0.0,
                            )
                #lonn, latn = m(lonn, latn)
                m.ax = fig.add_axes([0, 0, 1, 1])
                #fig.set_figsize_inches((20/m.aspect, 20.))
                fig.set_figheight(5)
                fig.set_figwidth(5/m.aspect)
                if "regrid" in actions:
                    import fvcom_compute.fvcom_stovepipe.regrid as regrid
                    wid = numpy.max((width, height))
                    size = (lonmax - lonmin) / wid
                    hi = (latmax - latmin) / size
                    hi = math.ceil(hi)
                    reglon = numpy.linspace(numpy.negative(lonmin), numpy.negative(lonmax), wid)
                    reglon = numpy.negative(reglon)
                    reglat = numpy.linspace(latmin, latmax, hi)

                    if "pcolor" in actions:
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        newvalues = regrid.regrid(mag, lonn, latn, nv, reglon, reglat, size)
                        reglon, reglat = numpy.meshgrid(reglon, reglat)
                        grid = reorderArray(newvalues, len(reglat[:,1]), len(reglon[1,:]))
                        ax = fig.add_subplot(111)
                        ax.pcolor(reglon, reglat, grid)
                    if "contours" in actions:
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        newvalues = regrid.regrid(mag, lonn, latn, nv, reglon, reglat, size)
                        reglon, reglat = numpy.meshgrid(reglon, reglat)
                        grid = reorderArray(newvalues, len(reglat[:,1]), len(reglon[1,:]))
                        ax = fig.add_subplot(111)
                        ax.contourf(reglon, reglat, grid)
                    if "vectors" in actions:
                        newv = regrid.regrid(v, lonn, latn, nv, reglon, reglat, size)
                        newu = regrid.regrid(u, lonn, latn, nv, reglon, reglat, size)
                        mag = numpy.power(newu.__abs__(), 2)+numpy.power(newv.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        ax = fig.add_subplot(111)
                        ax.quiver(reglon, reglat, newu, newv, mag, pivot='mid')
                else:
                    if "vectors" in actions:
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        #ax = fig.add_subplot(111)
                        #ax.quiver(lon, lat, u, v, mag, pivot='mid')
                        lon, lat = m(lon, lat)
                        m.quiver(lon, lat, u, v, mag, pivot='mid')
                        ax = Plot.gca()
                    elif "contours" in actions:
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        ax = fig.add_subplot(111)
                        ax.tricontourf(lon, lat, mag)
                        
                    elif  "facets" in actions:
                        #projection = request.GET["projection"]
                        #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                        #            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                        #            lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                        #            )
                        lonn, latn = m(lonn, latn)
                        #m.ax = fig.add_axes([0, 0, 1, 1])
                        
                        #fig.set_figheight(20)
                        #fig.set_figwidth(20/m.aspect)
                        #m.drawmeridians(numpy.arange(0,360,1), color='0.5',)
                        tri = Tri.Triangulation(lonn,latn,triangles=nv)
                        
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        #ax.tripcolor(lon, lat, mag, shading="")
                        #collection = PolyCollection(numpy.asarray([(lonn[node1],latn[node1]),(lonn[node2],latn[node2]),(lonn[node3],latn[node3])]))
                        verts = numpy.concatenate((tri.x[tri.triangles][...,numpy.newaxis],\
                                                tri.y[tri.triangles][...,numpy.newaxis]), axis=2)
                        collection = PolyCollection(verts)
                        collection.set_array(mag)
                        collection.set_edgecolor('none') 
                        
                        ax = Plot.gca()
                        
                        #m.add_collection(collection)
                        #ax = Plot.gca()
                        #m2.ax.add_collection(collection)
                        ax.add_collection(collection)

                lonmax, latmax = m(lonmax, latmax)
                lonmin, latmin = m(lonmin, latmin)
                ax.set_xlim(lonmin, lonmax)
                ax.set_ylim(latmin, latmax)
                ax.set_frame_on(False)
                ax.set_clip_on(False)
                ax.set_position([0,0,1,1])
                #Plot.yticks(visible=False)
                #Plot.xticks(visible=False)
                
                #Plot.axis('off')

                canvas = Plot.get_current_fig_manager().canvas
            
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
            
            elif "data" in actions:
                if "regrid" in actions:
                    #size = int(request.GET["size"])
                    wid = numpy.max((width, height))
                    size = (lonmax - lonmin) / wid
                    hi = (latmax - latmin) / size
                    hi = math.ceil(hi)
                    if "grid" in actions:
                        import fvcom_compute.fvcom_stovepipe.regrid as regrid
                        
                        response = HttpResponse(content_type='text/plain')
                        response['Content-Disposition'] = 'attachment; filename=fvcom.grd'
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        reglon = numpy.linspace(numpy.negative(lonmin), numpy.negative(lonmax), wid)
                        reglon = numpy.negative(reglon)
                        reglat = numpy.linspace(latmin, latmax, hi)
                        
                        #buffer = StringIO()
                        response.write(('ncols ' + str(len(reglon)) + '\n'))
                        response.write(('nrows ' + str(len(reglat)) + '\n'))
                        response.write(("xllcenter " + str(lonmin)) + '\n')
                        response.write(("yllcenter " + str(latmin)) + '\n')
                        response.write(('cellsize ' + str(size) + '\n'))
                        response.write(('NODATA_value ' + '-9999\n'))
                        
                        newvalues = regrid.regrid(mag, lonn, latn, nv, reglon, reglat, size)

                        #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
            
                        #dat = buffer.getvalue()
                        #buffer.close()
                        for i,v in enumerate(newvalues):
                            response.write(str(v))
                            test = float(i) / wid
                            if test.is_integer():
                                if i == 0:
                                    response.write(" ")
                                else:
                                    response.write('\n')
                            else: response.write(" ")
                            
                else:
                    if "nc" in actions:
                        response = HttpResponse(content_type='application/netcdf')
                        response['Content-Disposition'] = 'attachment; filename=fvcom.nc'
                        buffer = StringIO()
                        #rootgrp = Dataset(buffer, 'w', clobber=True)
                        #level = rootgrp.createDimension('level', 1)
                        #time = rootgrp.createDimension('time', 1)
                        #index = rootgrp.createDimension('cell', len(u))
                        #lonvar = rootgrp.createVariable('lon', 'f8',('cell',))
                        #latvar = rootgrp.createVariable('lat', 'f8',('cell',))
                        #uvar = rootgrp.createVariable('u','f4',('cell',))
                        #vvar = rootgrp.createVariable('v', 'f4',('cell',))
                        #magvar = rootgrp.createVariable('mag', 'f4', ('cell',))
                        rootgrp = scipy.io.netcdf_file(response, 'w')
                        rootgrp.createDimension('cell', len(u))
                        lonvar = rootgrp.createVariable('lon', 'f', ('cell',))
                        latvar = rootgrp.createVariable('lat', 'f', ('cell',))
                        uvar = rootgrp.createVariable('u', 's', ('cell',))
                        vvar = rootgrp.createVariable('v', 's', ('cell',))
                        magvar = rootgrp.createVariable('velocity', 's', ('cell',))
                        
                        
                        uvar[:] = u
                        vvar[:] = v
                        latvar[:] = numpy.asarray(lat)
                        lonvar[:] = numpy.asarray(lon)
                        
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        magvar[:] = mag
                        
                        rootgrp.close()
                        dat = buffer.getvalue()
                        buffer.close()
                        response.write(dat)
                    elif "text" in actions:
                        response = HttpResponse(content_type='text/csv')
                        response['Content-Disposition'] = 'filename=fvcom.txt'
                        X = numpy.asarray([lon,lat,u,v])
                        X = numpy.transpose(X)
                  
                        buffer = StringIO()
            
                        numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
            
                        dat = buffer.getvalue()
                        buffer.close()
                        response.write(dat)
                        
                    elif "mat" in actions:
                        response = HttpResponse(content_type='application/matlab-mat')
                        response['Content-Disposition'] = 'attachment; filename=fvcom.mat'
                        X = numpy.asarray([lon,lat,u,v])
                        X = numpy.transpose(X)
                  
                        buffer = StringIO()
            
                        scipy.io.savemat(buffer, { 'data' : X })
                        #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
            
                        dat = buffer.getvalue()
                        buffer.close()
                        response.write(dat)
                    elif "shp" in actions:
                        import shapefile
                        import zipfile
                        response = HttpResponse(content_type='application/x-zip')
                        response['Content-Disposition'] = 'attachment; filename=fvcom.zip'
                        w = shapefile.Writer(shapefile.POLYGON)
                        w.field('mag','F')
                        mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
                        mag = numpy.sqrt(mag)
                        
                        #for i,j in enumerate(lon):
                        #    w.point(j, lat[i])
                        #    w.record(mag[i])
                        for i,v in enumerate(index):
                            w.poly(parts=[[[lonn[nv[i, 0]], latn[nv[i, 0]]], \
                                           [lonn[nv[i, 1]], latn[nv[i, 1]]], \
                                           [lonn[nv[i, 2]], latn[nv[i, 2]]]]])
                            w.record(mag[i])

                        shp = StringIO()
                        shx = StringIO()
                        dbf = StringIO()
                        w.saveShp(shp)
                        w.saveShx(shx)
                        w.saveDbf(dbf)
                        z = zipfile.ZipFile(response, "w", zipfile.ZIP_STORED)
                        z.writestr("fvcom.shp", shp.getvalue())
                        z.writestr("fvcom.shx", shx.getvalue())
                        z.writestr("fvcom.dbf", dbf.getvalue())
                        z.close()
                    
        else: # for timeseries?
            timevalsqs = Time.objects.filter(date__gte=datestart).filter(date__lte=dateend).values("date")
            timevals = map(getVals, timevalsqs, numpy.ones(len(timesqs))*4)
            
            if "image" in actions:
                fig = Plot.figure()
                fig.set_alpha(0)
                ax = fig.add_subplot(111)

                #for direction in ["left", "right", "bottom", "top"]:
                #ax.set_frame_on(False)
                #ax.set_clip_on(False)
                #ax.set_position([0,0,1,1])
                #Plot.yticks(visible=False)
                #Plot.xticks(visible=False)
            
                #ax.set_xlim()
                #ax.set_ylim()
                
                canvas = Plot.get_current_fig_manager().canvas
            
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
            elif "data" in actions:
                if "nc" in actions:
                    pass
                elif "text" in actions:
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'filename=fvcom.txt'
                    X = numpy.asarray((u,v))
                    X = numpy.transpose(X)
              
                    buffer = StringIO()
        
                    numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
        
                    dat = buffer.getvalue()
                    buffer.close()
                    response.write(dat)
                elif "mat" in actions:
                    response = HttpResponse(content_type='application/matlab-mat')
                    response['Content-Disposition'] = 'attachment; filename=fvcom.mat'
                    X = numpy.asarray((u,v))
                    X = numpy.transpose(X)
              
                    buffer = StringIO()
        
                    scipy.io.savemat(buffer, { 'data' : X })
                    #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f')
        
                    dat = buffer.getvalue()
                    buffer.close()
                    response.write(dat)

    
    return response

def fvWps (request):
    pass
    return HttpResponse