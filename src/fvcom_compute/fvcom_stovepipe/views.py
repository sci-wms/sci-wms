'''
Created on Sep 1, 2011

@author: ACrosby
'''
# Create your views here.
from django.http import HttpResponse
import numpy
import netCDF4
from fvcom_compute.fvcom_stovepipe.models import Cell, Time, Node
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as Plot
from mpl_toolkits.basemap import Basemap
import datetime
from collections import deque
from StringIO import StringIO
import scipy.io
import math
import pp
import fvcom_compute.server_local_config as config
from matplotlib.backends.backend_agg import FigureCanvasAgg
import gc

def wmstest (request):
    return HttpResponse()

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

def crossdomain (request):
    f = open(config.staticspath + "crossdomain.xml")
    test = f.read()
    response = HttpResponse(content_type="text/xml")
    response.write(test)
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
    # make changes to server_local_config.py 
    if config.localdataset:
        url = config.localpath
    else:
        url = config.datasetpath
        
    
    width = float(request.GET["width"])
    height = float(request.GET["height"])
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
    
    colormap = request.GET["colormap"].lower()
    if request.GET["climits"][0] != "None":
        climits = [float(lim) for lim in request.GET["climits"]]
    else:
        climits = ["None", "None"]
        
    variables = request.GET["variables"].split(",")
    
    #if latmax == latmin:
    #    actions.append("timeseries")
    
    if "kml" in actions:
        pass
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
        ("shp" in actions) or \
        ("contours" in actions):
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
        time = range(50,51)
        #pv = deque()
        pvar = deque()
        def getvar(url, t, layer, var):
            nc = netCDF4.Dataset(url, 'r')
            # Expects 3d cell variables.
            return nc.variables[var][t, layer[0], :]

        #def getvvar(url, t, layer):
        #    nc = netCDF4.Dataset(url, 'r')
        #    return nc.variables["v"][t, layer[0], :]
        appendvar = pvar.append
        #appendv = pv.append
        job_server = pp.Server(4, ppservers=()) 

        # This is looping through time to avoid trying to download too much data from the server at once
        # and its SO SLOOOW, i think due to the append calls, maybe use np.concatenate>?
        t = time
        for var in variables:
            appendvar(job_server.submit(getvar, (url, t, layer, var),(), ("netCDF4", "numpy",))) 
            #appendv(job_server.submit(getvvar, (url, t, layer),(), ("netCDF4", "numpy",)))
        
        varis = deque()
        #v = deque()
        
        #[v.append(resultv()) for resultv in pv]
        #[u.append(resultu()) for resultu in pu]
        [varis.append(result()) for result in pvar]
        
        job_server.destroy() # important so that we dont keep spwaning workers on every call, real messy...
        
        var1 = numpy.asarray(varis[0])
        if len(varis) > 1:
            var2 = numpy.asarray(varis[1])
        
        index = numpy.asarray(index)
        if len(var1.shape) > 2:
            var1 = var1[:, :, index]
            try:
                var2 = var2[:, :, index]
            except:
                pass
        elif len(var1.shape) > 1:
            var1 = var1[:, index]
            try:
                var2 = var2[:, index]
            except:
                pass
        else: pass # or 1 timestep geographic...?...

        if latmin != latmax:
            # This is averaging in time over all timesteps downloaded
            if not "animate" in actions:
                if "average" in actions:
                    if len(var1.shape) > 2:
                        var1 = var1.mean(axis=0)
                        var1 = var1.mean(axis=0)
                        try:
                            var2 = var2.mean(axis=0)
                            var2 = var2.mean(axis=0)
                        except:
                            pass
                    elif len(var1.shape) > 1:
                        var1 = var1.mean(axis=0)
                        try:
                            var2 = var2.mean(axis=0)
                        except:
                            pass
                if "maximum" in actions:
                    if len(var1.shape) > 2:
                        var1 = var1.max(axis=0)
                        var1 = var1.max(axis=0)
                        try:
                            var2 = var2.max(axis=0)
                            var2 = var2.max(axis=0)
                        except:
                            pass
                    elif len(v.shape) > 1:
                        var1 = var1.max(axis=0)
                        try:
                            var2 = var2.max(axis=0)
                        except:
                            pass
            else: pass # will eventually add animations over time, instead of averages

            if "image" in actions:
                fig = Plot.figure(dpi=80, facecolor='none', edgecolor='none')
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
                #fig.set_figheight(5)
                #fig.set_figwidth(5/m.aspect)
                if "regrid" in actions:
                    """
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
                    """
                else:
                    if "vectors" in actions:
                        #fig.set_figheight(5)
                        fig.set_figwidth(height/80.0/m.aspect)
                        fig.set_figheight(height/80.0)
                        #fig.set_figwidth(width/80.0)

                        mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)

                        mag = numpy.sqrt(mag)
                        #ax = fig.add_subplot(111)
                        #ax.quiver(lon, lat, u, v, mag, pivot='mid')
                        lon, lat = m(lon, lat)
                        if climits[0] == "None":
                            CNorm = matplotlib.colors.Normalize()
                        else:
                            CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                            vmax=climits[1],
                                                            clip=True,
                                                            )
                        m.quiver(lon, lat, var1, var2, mag, 
                            pivot='mid',
                            units='xy',
                            cmap=colormap,
                            norm=CNorm,
                            )
                        ax = Plot.gca()
                        #fig.set_figheight(height/80.0)
                        #fig.set_figwidth(width/80.0)
                    elif "contours" in actions:
                        if len(variables) > 1:
                            mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
                        else:
                            mag = var1
                        mag = numpy.sqrt(mag)
                        ax = fig.add_subplot(111)
                        if climits[0] == "None":
                            CNorm = matplotlib.colors.Normalize()
                        else:
                            CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                            vmax=climits[1],
                                                            clip=True,
                                                            )
                        tri = Tri.Triangulation(lonn,latn,triangles=nv)
                        ax.tricontourf(tri, mag,
                            cmap=colormap,
                            norm=CNorm,
                            )
                        
                    elif  "facets" in actions:
                        #projection = request.GET["projection"]
                        #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                        #            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                        #            lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                        #            )
                        fig.set_figheight(height/80.0)
                        fig.set_figwidth(width/80.0)  
                        lonn, latn = m(lonn, latn)
                        #m.ax = fig.add_axes([0, 0, 1, 1])
                        
                        #fig.set_figheight(20)
                        #fig.set_figwidth(20/m.aspect)
                        #m.drawmeridians(numpy.arange(0,360,1), color='0.5',)
                        tri = Tri.Triangulation(lonn,latn,triangles=nv)
                        
                        if len(variables) > 1:
                            mag = numpy.sqrt(numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2))
                        else:
                            mag = numpy.sqrt(var1**2)
                            
                        #mag = numpy.sqrt(mag)
                        
                        #ax.tripcolor(lon, lat, mag, shading="")
                        #collection = PolyCollection(numpy.asarray([(lonn[node1],latn[node1]),(lonn[node2],latn[node2]),(lonn[node3],latn[node3])]))
                        verts = numpy.concatenate((tri.x[tri.triangles][...,numpy.newaxis],\
                                                tri.y[tri.triangles][...,numpy.newaxis]), axis=2)
                        
                        if climits[0] == "None":
                            CNorm = matplotlib.colors.Normalize()
                        else:
                            CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                            vmax=climits[1],
                                                            clip=True,
                                                            )
                        collection = PolyCollection(verts,
                                                    cmap=colormap, 
                                                    norm=CNorm,
                                                    )
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

                #canvas = Plot.get_current_fig_manager().canvas
                canvas = FigureCanvasAgg(fig)
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
                fig.clf()
                Plot.close()    
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

    gc.collect()
    return response

def fvWps (request):
    pass
    return HttpResponse
