'''
Created on Sep 1, 2011

@author: ACrosby
'''
# Create your views here.
from django.http import HttpResponse
import numpy
import netCDF4
#from fvcom_compute.fvcom_stovepipe.models import Cell, Time, Node
import matplotlib
matplotlib.use("Agg")
#from matplotlib import pyplot as Plot
from mpl_toolkits.basemap import Basemap
import datetime
from collections import deque
from StringIO import StringIO
#import scipy.io
import math
import pp
import fvcom_compute.server_local_config as config
from matplotlib.backends.backend_agg import FigureCanvasAgg
import gc
import time as timeobj
import bisect

def openlayers (request, filepath):

    f = open(config.staticspath + "openlayers/" + filepath)
    text = f.read()
    f.close()
    dict1 = { 'localsite':config.localhostip}
    #return dshorts.render_to_response(text, dict1)
    return HttpResponse(text, content_type='text')
    
def wmstest (request):
    import django.shortcuts as dshorts
    from django.template import Context, Template
    f = open(config.staticspath + "wms_openlayers_test.html")
    text = f.read()
    f.close()
    dict1 = Context({ 'localsite':config.localhostip})
    #return dshorts.render_to_response(text, dict1)
    return HttpResponse(Template(text).render(dict1))


def documentation (request):
    import django.shortcuts as dshorts
    #import fvcom_compute.server_local_config as config
    f = open(config.staticspath + "doc.txt")
    text = f.read()
    dict1 = { "textfile":text}
    return dshorts.render_to_response('docs.html', dict1)
"""
def test (request):
    import django.shortcuts as dshorts
    #import fvcom_compute.server_local_config as config
    f = open(config.staticspath + "test.txt")
    text = f.read()
    dict1 = { "textfile":text}
    return dshorts.render_to_response('docs.html', dict1)
"""
def wms (request, dataset):
    reqtype = request.GET['REQUEST']
    if reqtype.lower() == 'getmap':
        import fvcom_compute.fvcom_stovepipe.wms_handler as wms
        handler = wms.wms_handler(request)
        action_request = handler.make_action_request(request)
        response = fvDo(action_request, dataset)
    elif reqtype.lower() == 'getfeatureinfo':
        response =  getFeatureInfo(request, dataset)
    elif reqtype == 'getLegendGraphic':
        response = HttpResponse()
    elif reqtype == 'getCapabilities':
        response = HttpResponse()
    return response

def crossdomain (request):
    f = open(config.staticspath + "crossdomain.xml")
    test = f.read()
    response = HttpResponse(content_type="text/xml")
    response.write(test)
    return response
    
def getFeatureInfo(request, dataset):
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
    
    job_server = pp.Server(4, ppservers=()) 
       
    X = float(request.GET['X'])
    Y = float(request.GET['Y'])
    #VERSION = 
    box = request.GET["BBOX"]
    box = box.split(",")
    latmin = float(box[1])
    latmax = float(box[3])
    lonmin = float(box[0])
    lonmax = float(box[2])
    height = float(request.GET["HEIGHT"])
    width = float(request.GET["WIDTH"])
    styles = request.GET["STYLES"].split("_")
    #LAYERS = request.GET['LAYERS']
    #FORMAT =  request.GET['FORMAT']
    #TRANSPARENT = 
    QUERY_LAYERS = request.GET['QUERY_LAYERS'].split(",")
    QUERY_LAYERS.append("time")
    INFO_FORMAT = "text/plain" # request.GET['INFO_FORMAT']
    projection = 'merc'#request.GET['SRS']
    TIME = request.GET['TIME']
    elevation = request.GET['ELEVATION']
    
    from matplotlib.figure import Figure
    fig = Figure(dpi=80, facecolor='none', edgecolor='none')
    fig.set_alpha(0)

    m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                urcrnrlon=lonmax, urcrnrlat=latmax,
                projection=projection,                             
                resolution=None,
                lat_ts = 0.0,
                suppress_ticks=True)
    m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])
    fig.set_figheight(height/80.0)
    fig.set_figwidth(width/80.0) 
    
    lon, lat = m(X, Y, inverse=True)
    
    topology = netCDF4.Dataset(config.topologypath + dataset + '.nc')

    if 'node' in styles:
        #nv = topology.variables['nv'][:,index].T-1
        lats = topology.variables['lat'][:]
        lons = topology.variables['lon'][:]
    else:
        lats = topology.variables['latc'][:]
        lons = topology.variables['lonc'][:]
    
    lengths = map(haversine, numpy.ones(len(lons))*lat, \
                          numpy.ones(len(lons))*lon, lats, lons)
    min = numpy.asarray(lengths)
    min = numpy.min(min)
    index = lengths.index(min)

    
    if config.localdataset:
        time = [1]
    else:
        TIMES = TIME.split("/")
        datestart = datetime.datetime.strptime(TIMES[0], "%Y-%m-%dT%H:%M:%S" )
        dateend = datetime.datetime.strptime(TIMES[1], "%Y-%m-%dT%H:%M:%S" )
        times = topology.variables['time'][:]
        time_units = topology.variables['time'].units
        datestart = netCDF4.date2num(datestart, units=time_units)
        dateend = netCDF4.date2num(dateend, units=time_units)
        time1 = bisect.bisect_right(times, datestart) - 1
        time2 = bisect.bisect_right(times, dateend) - 1
        time = range(time1, time2)
        
    pvar = deque()
    def getvar(url, t, layer, var, ind):
        nc = netCDF4.Dataset(url, 'r')
        if var == "time":
            return nc.variables[var][t]
        else:
            # Expects 3d cell variables.
            if len(nc.variables[var].shape) == 3:
                return nc.variables[var][t, layer[0], ind]
            elif len(nc.variables[var].shape) == 2:
                return nc.variables[var][t, ind]
            elif len(nc.variables[var].shape) == 1:
                return nc.variables[var][ind]
            
    if config.localdataset:
        url = config.localpath[dataset]
        time = range(1,30)
        elevation = [5]
    else:
        url = config.datasetpath[dataset]
    appendvar = pvar.append
    for var in QUERY_LAYERS:
        appendvar(job_server.submit(getvar, (url, time, elevation, var, index),(), ("netCDF4", "numpy",))) 
    varis = deque()
    [varis.append(result()) for result in pvar]
    #var1 = numpy.asarray(varis[0])
    #if len(varis) > 1:
    #    var2 = numpy.asarray(varis[1])
        
    #response = HttpResponse(content_type='text/csv')
    response = HttpResponse()
    #response['Content-Disposition'] = 'filename=fvcom.txt'
    #if len(varis) >1:
    #    X = numpy.asarray([var1,var2])
    #else:
    #    X = numpy.asarrray([var1])
    X = numpy.asarray([var for var in varis])
    X = numpy.transpose(X)

    buffer = StringIO()

    numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f', newline="|")

    dat = buffer.getvalue()
    buffer.close()
    response.write(dat)
    return response
        
        
"""
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
"""

def fvDo (request, dataset='30yr_gom3'):
    '''
    Request a set of functionalities, any subset of the following:
    1) WMS Style Image Request
    2) WMS Style Image Request for Vectors
    3) Regridding
    4) Request t/lat/lon/z chunk
    5) Do averaging
    With appropriate parameters for each (parameters my overlap).
    '''
    
    
    totaltimer = timeobj.time()
    """
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
    """
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
        url = config.localpath[dataset]
    else:
        url = config.datasetpath[dataset]
        

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
    
    colormap = request.GET["colormap"]#.lower()
    if request.GET["climits"][0] != "None":
        climits = [float(lim) for lim in request.GET["climits"]]
    else:
        climits = ["None", "None"]
    magnitude = bool(request.GET["magnitude"])
    topology_type = request.GET["topologytype"]
        
    variables = request.GET["variables"].split(",")
    #print "request parse"
    #if latmax == latmin:
    #    actions.append("timeseries")
    
    if "kml" in actions:
        pass
    else:
        
        topology = netCDF4.Dataset(config.topologypath + dataset + '.nc')
        
        #if topology_type.lower() == "cell":
        if latmax != latmin:
            """
            #geobb = Cell.objects.filter(lat__lte=latmax).filter(lat__gte=latmin)\
            #    .filter(lon__lte=lonmax).filter(lon__gte=lonmin)
            geobb = Cell.objects.filter(lat__lte=latmax+.18).filter(lat__gte=latmin-.18)\
                .filter(lon__lte=lonmax+.18).filter(lon__gte=lonmin-.18)
            indexqs = geobb.values("index")
            latqs = geobb.values("lat")
            lonqs = geobb.values("lon")
            
            index = map(getVals, indexqs, numpy.ones(len(indexqs)))
            lat = map(getVals, latqs, numpy.ones(len(indexqs))*2)
            lon = map(getVals, lonqs, numpy.ones(len(indexqs))*3)
            """
            lat = topology.variables['latc'][:]
            lon = topology.variables['lonc'][:]
            

            index = numpy.asarray(numpy.where(
                (lat <= latmax+.18) & (lat >= latmin-.18) &
                (lon <= lonmax+.18) & (lon >= lonmin-.18),)).squeeze()
            
            lat = lat[index]
            lon = lon[index]

            
        else:
            pass
            """
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
            """
        
        if len(index) > 0:
            job_server = pp.Server(4, ppservers=()) 
            #print "cell database"
            if ("facets" in actions) or \
            ("regrid" in actions) or \
            ("shp" in actions) or \
            ("contours" in actions) or \
            ("interpolate" in actions) or \
            ("filledcontours" in actions) or \
            ("pcolor" in actions) or \
            (topology_type.lower()=='node'):

                #if topology_type.lower() == "cell":
                from matplotlib.collections import PolyCollection
                import matplotlib.tri as Tri
                
                """
                node1qs = geobb.values("node1")
                node2qs = geobb.values("node2")
                node3qs = geobb.values("node3")
                nodesqs = Node.objects.all().values()
                latnqs = nodesqs.values("lat")
                lonnqs = nodesqs.values("lon")
                latn = map(getVals, latnqs, numpy.ones(len(latnqs))*2)
                lonn = map(getVals, lonnqs, numpy.ones(len(latnqs))*3)
                 
                node1 = map(getVals, node1qs, numpy.ones(len(indexqs))*5)
                node2 = map(getVals, node2qs, numpy.ones(len(indexqs))*6)
                node3 = map(getVals, node3qs, numpy.ones(len(indexqs))*7)
                nv = numpy.asarray([node1, node2, node3],'int64')
                nv = numpy.transpose(nv)
                if topology_type.lower() == "node":
                    index = range(len(latn))
                    latn = numpy.asarray(latn)
                    lonn = numpy.asarray(lonn)
                else:
                    latn = numpy.asarray(latn)
                    lonn = numpy.asarray(lonn)
                #trijob = job_server.submit(gettri, (lonn, latn, nv),(), ("netCDF4", "numpy","matplotlib"))
                """
                
                #nv = topology.variables['nv'][:,index].T-1
                nvtemp = topology.variables['nv'][:,:]#.T-1
                nv = nvtemp[:,index].T-1
                latn = topology.variables['lat'][:]
                lonn = topology.variables['lon'][:]
                if topology_type.lower() == "node":
                    index = range(len(latn))
            else:
                nv = None

                
            
            
            datestart = datetime.datetime.strptime( datestart, "%Y-%m-%dT%H:%M:%S" )
            #dateend = datetime.datetime.strptime( dateend, "%Y-%m-%dT%H:%M:%S" )
            """
            timesqs = Time.objects.filter(date__gte=datestart).filter(date__lte=dateend).values("index")
            #time = map(getVals, timesqs, numpy.ones(len(timesqs))*1) # commented out for testing of local speed
            """
            times = topology.variables['time'][:]
            datestart = netCDF4.date2num(datestart,
                units=topology.variables['time'].units)
            #dateend = date2num(dateend, units=times.units)
            #print times
            #print datestart
            time = bisect.bisect_right(times, datestart) - 1
            if config.localdataset:
                time = [1]
            else:
                time = [time]
            
            print time
            
            pvar = deque()
            def getvar(url, t, layer, var):
                nc = netCDF4.Dataset(url, 'r')
                
                # Expects 3d cell variables.
                if len(nc.variables[var].shape) == 3:
                    return nc.variables[var][t, layer[0], :]
                elif len(nc.variables[var].shape) == 2:
                    return nc.variables[var][t, :]
                elif len(nc.variables[var].shape) == 1:
                    return nc.variables[var][:]
            #def getvvar(url, t, layer):
            #    nc = netCDF4.Dataset(url, 'r')
            #    return nc.variables["v"][t, layer[0], :]
            appendvar = pvar.append
            #appendv = pv.append
            #job_server = pp.Server(4, ppservers=()) 
            
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
            
            #job_server.destroy() # important so that we dont keep spwaning workers on every call, real messy...
            
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
            #print "print netcdf access"
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
                        elif len(var1.shape) > 1:
                            var1 = var1.max(axis=0)
                            try:
                                var2 = var2.max(axis=0)
                            except:
                                pass
                else: pass # will eventually add animations over time, instead of averages
                #print "done math"
        
                if "image" in actions:
                    from matplotlib.figure import Figure
                    fig = Figure(dpi=80, facecolor='none', edgecolor='none')
                    fig.set_alpha(0)
                    #ax = fig.add_subplot(111)
                    projection = request.GET["projection"]
                    
                    
                    if ('contours' in actions) or \
                        ('filledcontours' in actions):
                        if topology_type == 'cell':
                            m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                                urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                                #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                                resolution='c',
                                lat_ts = 0.0,
                                suppress_ticks=True)
                        else:
                            m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                                urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                                #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                                resolution=None,
                                lat_ts = 0.0,
                                suppress_ticks=True)
                    elif ('pcolor' in actions):
                        m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                                urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                                #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                                resolution='c',
                                lat_ts = 0.0,
                                suppress_ticks=True)
                    else:
                        m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                                urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                                #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                                resolution=None,
                                lat_ts = 0.0,
                                suppress_ticks=True)
                    """
                    m = Basemap(llcrnrx=lonmin, llcrnry=latmin, 
                                urcrnrx=lonmax, urcrnry=latmax, projection=projection,
                                #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                                lat_ts = 0.0,
                                )
                    """
                    #lonn, latn = m(lonn, latn)
                    m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])
                    #fig.set_figsize_inches((20/m.aspect, 20.))
                    #fig.set_figheight(5)
                    #fig.set_figwidth(5/m.aspect)
                    #print "createfig"
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
                        """
                        if "interpolate" in actions:
                            
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  

                            lonn, latn = m(lonn, latn)

                            tri = Tri.Triangulation(lonn,latn,triangles=nv)

                            #tri = trijob()
       
                            if len(variables) > 1:
                                mag = numpy.sqrt(numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2))
                            else:
                                if magnitude:
                                    mag = numpy.sqrt(var1**2)
                                else:
                                    mag = var1

                            #verts = numpy.concatenate((tri.x[tri.triangles][...,numpy.newaxis],\
                            #                        tri.y[tri.triangles][...,numpy.newaxis]), axis=2)
                            
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                                vmax=climits[1],
                                                                clip=True,
                                                                )
                                                                
                            m.ax.tripcolor(tri, mag,
                                           shading="",
                                           norm=CNorm,
                                           cmap=colormap,
                                           )

                            #ax = Plot.gca()
                            #ax = m.ax
                        """    
                        if "vectors" in actions:
                            #fig.set_figheight(5)
                            fig.set_figwidth(height/80.0/m.aspect)
                            fig.set_figheight(height/80.0)
                            #fig.set_figwidth(width/80.0)
                            
                            mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)

                            mag = numpy.sqrt(mag)
                            #ax = fig.add_subplot(111)
                            #ax.quiver(lon, lat, u, v, mag, pivot='mid')
                            if topology_type == 'cell':
                                lon, lat = m(lon, lat)
                            else:
                                lon, lat = m(lonn, latn)
                                
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                                vmax=climits[1],
                                                                clip=True,
                                                                )
                            if nv is not None:
                                n = numpy.unique(nv)
                                m.quiver(lon[n], lat[n], var1[n], var2[n], mag[n], 
                                    pivot='mid',
                                    units='xy',
                                    cmap=colormap,
                                    norm=CNorm,
                                    )
                            else:
                                m.quiver(lon, lat, var1, var2, mag, 
                                    pivot='mid',
                                    units='xy',
                                    cmap=colormap,
                                    norm=CNorm,
                                    )

                        if "barbs" in actions:
                            #fig.set_figheight(5)
                            fig.set_figwidth(height/80.0/m.aspect)
                            fig.set_figheight(height/80.0)
                            #fig.set_figwidth(width/80.0)
                            
                            mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)

                            mag = numpy.sqrt(mag)
                            #ax = fig.add_subplot(111)
                            #ax.quiver(lon, lat, u, v, mag, pivot='mid')
                            if topology_type == 'cell':
                                lon, lat = m(lon, lat)
                            else:
                                lon, lat = m(lonn, latn)
                                
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                                full = 10.#.2
                                flag = 50.#1.
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                                vmax=climits[1],
                                                                clip=True,
                                                                )
                                full = climits[0]
                                flag = climits[1]
                            if nv is not None:
                                n = numpy.unique(nv)
                                m.ax.barbs(lon[n], lat[n], var1[n], var2[n], mag[n],
                                    length=5.8,
                                    pivot='middle',
                                    barb_increments=dict(half=full/2., full=full, flag=flag),
                                    #units='xy',
                                    #cmap=colormap,
                                    #norm=CNorm,
                                    )
                            else:
                                m.ax.barbs(lon, lat, var1, var2, mag,
                                    length=5.8,
                                    pivot='middle',
                                    barb_increments=dict(half=full/2., full=full, flag=flag),
                                    #units='xy',
                                    #cmap=colormap,
                                    #norm=CNorm,
                                    )   
                            

                            
                        elif "contours" in actions:
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  
                            #lon, lat = m(lon, lat)
                            #lonn, latn = m(lonn, latn)
                            if len(variables) > 1:
                                mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
                                mag = numpy.sqrt(mag)
                            else:
                                if magnitude:
                                    mag = numpy.abs(var1)
                                else:
                                    mag = var1
                            
                            #ax = fig.add_subplot(111)
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                                levs = None
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],                             vmax=climits[1],clip=True,
                                                                )
                                levs = numpy.arange(0, 12)*(climits[1]-climits[0])/10
                            #tri = Tri.Triangulation(lonn,latn,triangles=nv)
                            #ax.tricontourf(tri, mag,
                            #    cmap=colormap,
                            #    norm=CNorm,
                            #    )\
                            
                            #m.contour(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, levels=levs)
                            if topology_type == 'cell':
                                print dir(m)
                                lon, lat = m(lon, lat)
                                trid = Tri.Triangulation(lon, lat)
                                mask = []
                                for triangs in trid.triangles:
                                    mask.append(m.is_land(
                                    lon[triangs].mean(),
                                    lat[triangs].mean()))
                                trid.set_mask(mask)
                                m.ax.tricontour(trid, mag, norm=CNorm, levels=levs, antialiased=True)
                                
                                #qq = m.contourf(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, levels=levs, antialiased=True)
                            else:
                                lonn, latn = m(lonn, latn)
                                tri = Tri.Triangulation(lonn, latn, triangles=nv)
                                m.ax.tricontour(tri, mag, norm=CNorm, levels=levs, antialiased=True)           
                            
                        elif "filledcontours" in actions:
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  
                            
                            if len(variables) > 1:
                                mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2) 
                                mag = numpy.sqrt(mag)
                            else:
                                if magnitude:
                                    mag = numpy.abs(var1)
                                else:
                                    mag = var1
                            
                            #ax = fig.add_subplot(111)
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                                levs = None
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],                             vmax=climits[1],clip=False,
                                                                    )
                                levs = numpy.arange(1, 12)*(climits[1]-(climits[0]))/10
                                levs = numpy.hstack(([-99999], levs, [99999]))
      
                            #import matplotlib.delaunay as Trid
                            #trid = Trid.Triangulation(lon,lat)
                            
                            #print dir(Trid.LinearInterpolator())
                            #print dir(tri)
                            #verts = numpy.concatenate((tri.x[tri.triangles][...,numpy.newaxis],\
                            #                        tri.y[tri.triangles][...,numpy.newaxis]), axis=2)
                            
                            #collection = PolyCollection(verts,
                            #                            cmap=colormap, 
                            #                            norm=CNorm,
                            #                           )
                            #interp = tri.nn_interpolator(numpy.asarray(mag))
                            #interp = Trid.NNInterpolator(tri, numpy.asarray(mag))
                            #print dir(interp)
                            #print interp.z
                            #cent = trid.circumcenters
                            #print dir(collection)
                            #print collection.contains(cent[:,0], cent[:,1])
                            
                            if topology_type == 'cell':
                                #print dir(m)
                                lon, lat = m(lon, lat)
                                trid = Tri.Triangulation(lon, lat)
                                #tri = Tri.Triangulation(lonn, latn, triangles=nv)
                                mask = []
                                for triangs in trid.triangles:
                                    mask.append(m.is_land(
                                    lon[triangs].mean(),
                                    lat[triangs].mean()))
                                trid.set_mask(mask)
                                m.ax.tricontourf(trid, mag, norm=CNorm, levels=levs, antialiased=True)
                                
                                #qq = m.contourf(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, levels=levs, antialiased=True)
                            else:
                                lonn, latn = m(lonn, latn)
                                tri = Tri.Triangulation(lonn, latn, triangles=nv)
                                m.ax.tricontourf(tri, mag, norm=CNorm, levels=levs, antialiased=True)           
                            #print dir(collection)
                            #paths = collection.get_paths()
                            #xrms = collection.get_transforms()
                            #temp = []
                            
                            
                        elif "pcolor" in actions:
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  
                            lon, lat = m(lon, lat)
                            
                            if len(variables) > 1:
                                mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
                                mag = numpy.sqrt(mag)
                            else:
                                if magnitude:
                                    mag = numpy.abs(var1)
                                else:
                                    mag = var1
                            
                            #ax = fig.add_subplot(111)
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],                             vmax=climits[1],clip=True,
                                                                )
                            #tri = Tri.Triangulation(lonn,latn,triangles=nv)
                            #ax.tricontourf(tri, mag,
                            #    cmap=colormap,
                            #    norm=CNorm,
                            #    )\
                           
                            #m.pcolor(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, rasterized=True)
                            #xi = numpy.arange(lon.min(), lon.max(), 1000)
                            #yi = numpy.arange(lat.min(), lat.max(), 1000)
                            #print "lon " + str(lonmax-lonmin)
                            if lonmax-lonmin < 1:
                                xi = numpy.arange(m.xmin, m.xmax, 120)
                                yi = numpy.arange(m.ymin, m.ymax, 120)
                            elif lonmax-lonmin < 3:
                                xi = numpy.arange(m.xmin, m.xmax, 200)
                                yi = numpy.arange(m.ymin, m.ymax, 200)
                            elif lonmax-lonmin < 9:
                                xi = numpy.arange(m.xmin, m.xmax, 1000)
                                yi = numpy.arange(m.ymin, m.ymax, 1000)
                            else:
                                xi = numpy.arange(m.xmin, m.xmax, 2500)
                                yi = numpy.arange(m.ymin, m.ymax, 2500)
                            

                            from matplotlib.mlab import griddata
                            
                            #nx = int((m.xmax-m.xmin)/5000.)+1
                            #ny = int((m.ymax-m.ymin)/5000.)+1
                            
                            #if topology_type == 'cell':
                            zi = griddata(lon, lat, mag, xi, yi, interp='nn')
                            #else:
                            #    lon, lat = m(lonn, latn)
                            #    zi = griddata(lon, lat, mag, xi, yi, interp='nn')
                                #lonn, latn = m(lonn, latn)

                            #dat = m.transform_scalar(mag, xi, yi, nx, ny)
                            #mask = numpy.ndarray(shape=zi.shape)
                            for i,x in enumerate(xi):
                                for j,y in enumerate(yi):
                                    if m.is_land(x,y):
                                        zi[j,i] = numpy.nan
                            m.imshow(zi, norm=CNorm, cmap=colormap)
                            
                        elif  "facets" in actions:
                            #projection = request.GET["projection"]
                            #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                            #            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                            #            lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                            #            )
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  
                            lonn, latn = m(lonn, latn)
                            tri = Tri.Triangulation(lonn,latn,triangles=nv)
                            if len(variables) > 1:
                                mag = numpy.sqrt(numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2))
                            else:
                                if magnitude:
                                    mag = numpy.sqrt(var1**2)
                                else:
                                    mag = var1
                                    
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                                vmax=climits[1],
                                                                clip=True,
                                                                )
                                                                    
                            if topology_type == 'cell':
                                verts = numpy.concatenate((tri.x[tri.triangles][...,numpy.newaxis],\
                                                        tri.y[tri.triangles][...,numpy.newaxis]), axis=2)
                                
                                
                                collection = PolyCollection(verts,
                                                            cmap=colormap, 
                                                            norm=CNorm,
                                                            )
                                collection.set_array(mag)
                                collection.set_edgecolor('none')

                                m.ax.add_collection(collection)
                                #print "adding collection"
                            else:
                                m.ax.tripcolor(tri, mag,
                                               shading="",
                                               norm=CNorm,
                                               cmap=colormap,
                                               )
                            
                    lonmax, latmax = m(lonmax, latmax)
                    lonmin, latmin = m(lonmin, latmin)
                    m.ax.set_xlim(lonmin, lonmax)
                    m.ax.set_ylim(latmin, latmax)
                    m.ax.set_frame_on(False)
                    m.ax.set_clip_on(False)
                    m.ax.set_position([0,0,1,1])
                    #Plot.yticks(visible=False)
                    #Plot.xticks(visible=False)
                    
                    #Plot.axis('off')

                    #canvas = Plot.get_current_fig_manager().canvas
                    
                    canvas = FigureCanvasAgg(fig)
                    response = HttpResponse(content_type='image/png')
                    #response = HttpResponse(content_type="image/svg+xml")
                    #fig.savefig(response, format='svg')
                    #canvas.print_figure(response, dpi=80, facecolor=None, edgecolor=None)
                    canvas.print_png(response)
                    #print "print png"
                    #fig.clf()
                    #Plot.close()   
                     
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
                            mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
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
                            #z = zipfile.ZipFile(response, "w", zipfile.ZIP_STORED)
                            z = zipfile.ZipFile('/home/acrosby/alexsfvcomshape.zip', 'w', zipfile.ZIP_STORED)
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
            job_server.destroy() # important so that we dont keep spwaning workers on every call, real messy...
                        
        else:
            from matplotlib.figure import Figure
            fig = Figure(dpi=5, facecolor='none', edgecolor='none')
            fig.set_alpha(0)
            projection = request.GET["projection"]
            """
            m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                        urcrnrlon=lonmax, urcrnrlat=latmax,
                        projection=projection,
                        lat_ts = 0.0,
                        suppress_ticks=True)
            """ 
            ax = fig.add_axes([0, 0, 1, 1])
            fig.set_figheight(height/5.0)
            fig.set_figwidth(width/5.0)
            ax.set_frame_on(False)
            ax.set_clip_on(False)
            ax.set_position([0,0,1,1])
            canvas = FigureCanvasAgg(fig)
            response = HttpResponse(content_type='image/png')
            canvas.print_png(response)
            
    
    gc.collect()
    print timeobj.time() - totaltimer
    return response

def fvWps (request):
    pass
    return HttpResponse
