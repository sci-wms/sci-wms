'''
Created on Sep 1, 2011

@author: ACrosby
'''
# Create your views here.
from django.http import HttpResponse
import numpy
import netCDF4
from fvcom_compute.fvcom_stovepipe.models import Cell, Time, Node
#from matplotlib import pyplot as Plot ###
#from mpl_toolkits.basemap import Basemap ###
import datetime
from collections import deque
#from StringIO import StringIO
#import scipy.io ###
import math
import pp
import fvcom_compute.server_local_config as config

def wmstest (request):
    from fvcom_compute.fvcom_stovepipe import openlayers
    response = openlayers();
    return HttpResponse(response)

def documentation (request):
    import django.shortcuts as dshorts
    f = open(config.staticspath + "doc.txt")
    text = f.read()
    dict = { "textfile":text}
    return dshorts.render_to_response('docs.html', dict)

def test (request):
    import django.shortcuts as dshorts
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
        
    response = HttpResponse()
    response.write("done!")
    return response


def fvDo (request):
    '''
    
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
        from fvcom_compute.fvcom_stovepipe import kmz_response
        response, request, actions = kmz_response( request, actions, lonmax, lonmin, latmax, latmin )
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
            #what the fuck am i doing here//
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
            #from matplotlib.collections import PolyCollection
            #import matplotlib.tri as Tri
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
           
        datestart = datetime.datetime.strptime( datestart, "%Y-%m-%dT%H:%M:%S" )
        dateend = datetime.datetime.strptime( dateend, "%Y-%m-%dT%H:%M:%S" )
        timesqs = Time.objects.filter(date__gte=datestart).filter(date__lte=dateend).values("index")
        #time = map(getVals, timesqs, numpy.ones(len(timesqs))*1) # commented out for testing of local speed
        time = range(50) # for testing
        pv = deque()
        pu = deque()
        def getuvar(url, t, layer):
            nc = netCDF4.Dataset(url)
            return nc.variables["u"][t, layer[0], :] # also should be including all the layers...
        def getvvar(url, t, layer):
            nc = netCDF4.Dataset(url)
            return nc.variables["v"][t, layer[0], :] # also should be including all the layers...
        appendu = pu.append
        appendv = pv.append
        job_server = pp.Server(16, ppservers=()) # parallelpython, need to find good balance of workers
        

        # This is looping through time to avoid trying to download too much data from the server at once
        # and its SO SLOOOW, i think due to the append calls, maybe use np.concatenate>?
        for t in time:
            appendu(job_server.submit(getuvar, (url, t, layer),(), ("netCDF4", "numpy",))) 
            appendv(job_server.submit(getvvar, (url, t, layer),(), ("netCDF4", "numpy",)))
        
        u = deque()
        v = deque()
        
        [v.append(resultv()) for resultv in pv]
        [u.append(resultu()) for resultu in pu]
        job_server.destroy() # important so that we dont keep spwaning workers on every call, real messy...
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
                from fvcom_compute.fvcom_stovepipe import image_response
                response = image_response( request, actions, u, v, width, height, lonmax, lonmin, latmax, latmin, index, lon, lat, lonn, latn, nv)
            
            elif "data" in actions:
                from fvcom_compute.fvcom_stovepipe import data_response
                response = data_response( actions, u, v, width, height, lonmax, lonmin, latmax, latmin, index, lon, lat, lonn, latn, nv )
                    
        else: # for timeseries?
            #timeseries
            pass

    
    return response

def fvWps (request):
    pass
    return HttpResponse