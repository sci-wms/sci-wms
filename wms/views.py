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

Created on Sep 1, 2011

@author: ACrosby
'''

import os
import json
import bisect
import datetime
from urlparse import urlparse

import numpy
import netCDF4

# Import from matplotlib and set backend
import matplotlib
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Other random "from" imports
from rtree import index as rindex
from collections import deque
from StringIO import StringIO  # will be deprecated in Python3, use io.byteIO instead

from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.template.response import TemplateResponse
from django.core import serializers
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.cache import cache_page

from pyugrid import UGrid
from pysgrid import from_nc_dataset

from wms.models import Dataset, Server
from wms.utils import get_layer_from_request
from wms import wms_handler
from wms import logger


@cache_page(604800)
def crossdomain(request):
    with open(os.path.join(settings.PROJECT_ROOT, "static", "sciwms", "crossdomain.xml")) as f:
        response = HttpResponse(content_type="text/xml")
        response.write(f.read())
    return response


@cache_page(604800)
def favicon(request):
    with open(os.path.join(settings.PROJECT_ROOT, "static", "sciwms", "favicon.ico")) as f:
        response = HttpResponse(content_type="image/x-icon")
        response.write(f.read())
    return response


def datasets(request):
    from django.core import serializers
    datasets = Dataset.objects.all()
    data = serializers.serialize('json', datasets)
    return HttpResponse(data, content_type='application/json')


def index(request):
    datasets = Dataset.objects.all()
    context = { "datasets" : datasets }
    return TemplateResponse(request, 'wms/index.html', context)


def groups(request):
    return HttpResponse('ok')


def authenticate_view(request):
    if request.user.is_authenticated():
        return True

    if request.method == 'POST':
        uname = request.POST.get('username', None)
        passw = request.POST.get('password', None)
    elif request.method == 'GET':
        uname = request.GET.get('username', None)
        passw = request.GET.get('password', None)

    user = authenticate(username=uname, password=passw)

    if user is not None and user.is_active:
        login(request, user)
        return True
    else:
        return False

def logout_view(request):
    logout(request)

def update_dataset(request, dataset):
    if authenticate_view(request):
        if dataset is None:
            return HttpResponse(json.dumps({ "message" : "Please include 'dataset' parameter in GET request." }), content_type='application/json')
        else:
            d = Dataset.objects.get(slug=dataset)
            d.update_cache(force=True)
            return HttpResponse(json.dumps({ "message" : "Scheduled" }), content_type='application/json')
    else:
        return HttpResponse(json.dumps({ "message" : "Authentication failed, please login to the admin console first or pass login credentials to the GET request ('username' and 'password')" }), content_type='application/json')

    logout_view(request)


def normalize_get_params(request):
    gettemp = request.GET.copy()
    for key in request.GET.iterkeys():
        gettemp[key.lower()] = request.GET[key]
    request.GET = gettemp
    return request


def getFeatureInfo(request, dataset):
    """
     /wms/GOM3/?ELEVATION=1&LAYERS=temp&FORMAT=image/png&TRANSPARENT=TRUE&STYLES=facets_average_jet_0_32_node_False&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&SRS=EPSG:3857&BBOX=-7949675.196111,5078194.822174,-7934884.63114,5088628.476533&X=387&Y=196&INFO_FORMAT=text/csv&WIDTH=774&HEIGHT=546&QUERY_LAYERS=salinity&TIME=2012-08-14T00:00:00/2012-08-16T00:00:00
    """
    from datetime import date
    from mpl_toolkits.basemap import pyproj

    dataset = Dataset.objects.get(slug=dataset)

    X = float(request.GET['x'])
    Y = float(request.GET['y'])
    box = request.GET["bbox"]
    box = box.split(",")
    latmin = float(box[1])
    latmax = float(box[3])
    lonmin = float(box[0])
    lonmax = float(box[2])
    height = float(request.GET["height"])
    width = float(request.GET["width"])
    styles = request.GET["styles"].split(",")[0].split("_")
    QUERY_LAYERS = request.GET['query_layers'].split(",")

    try:
        elevation = int(request.GET['elevation'])
    #print elevation
    except:
        elevation = 0

    mi = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs ")
    # Find the gfi position as lat/lon, assumes 0,0 is ul corner of map
    lon, lat = mi(lonmin+((lonmax-lonmin)*(X/width)),
                  latmax-((latmax-latmin)*(Y/height)),
                  inverse=True)
    lonmin, latmin = mi(lonmin, latmin, inverse=True)
    lonmax, latmax = mi(lonmax, latmax, inverse=True)

    topology = netCDF4.Dataset(dataset.topology_file)
    ug = UGrid()
    try:
        topology_grid = ug.from_nc_dataset(topology)
    except:
        topology_grid = None
    # gridtype = topology.grid

    try:
        mesh_name = topology_grid.mesh_name
    except AttributeError:
        mesh_name = None

    if mesh_name is not None:
        grid_type = 'ugrid'
    else:
        grid_type = 'sgrid'

    if grid_type == 'ugrid':
        test_index = 0
        if 'node' in styles:
            tree = rindex.Index(dataset.node_tree_root)
            #lats = topology.variables['lat'][:]
            #lons = topology.variables['lon'][:]
            nindex = list(tree.nearest((lon, lat, lon, lat), 1, objects=True))
        else:
            from shapely.geometry import Polygon, Point
            tree = rindex.Index(dataset.cell_tree_root)
            #lats = topology.variables['latc'][:]
            #lons = topology.variables['lonc'][:]
            nindex = list(tree.nearest((lon, lat, lon, lat), 4, objects=True))
            test_point = Point(lon, lat)
            test = -1
            for ii, i in enumerate(nindex):
                lons = i.object[0]
                lats = i.object[1]
                test_cell = Polygon([(lons[0], lats[0]),
                                    (lons[1],  lats[1]),
                                    (lons[2],  lats[2]),
                                    (lons[0],  lats[0]),
                                    ])
                if test_cell.contains(test_point):
                    test_index = ii
                    test = i.id
            if test == -1:
                nindex = list(tree.nearest((lon, lat, lon, lat), 1, objects=True))
        selected_longitude, selected_latitude = tuple(nindex[test_index].bbox[:2])
        index = nindex[test_index].id
        tree.close()
    else:
        tree = rindex.Index(dataset.node_tree_root)
        if grid_type == 'sgrid':
            sg = from_nc_dataset(topology)
            sg_centers = sg.centers
            lats = sg_centers[..., 1]
            lons = sg_centers[..., 0]
        else:
            lats = topology.variables['lat'][:]
            lons = topology.variables['lon'][:]
        nindex = list(tree.nearest((lon, lat, lon, lat), 1, objects=True))
        selected_longitude, selected_latitude = lons[nindex[0].object[0], nindex[0].object[1]][0], lats[nindex[0].object[0], nindex[0].object[1]][0]
        index = nindex[0].object
        tree.close()
        index = numpy.asarray(index)

    try:
        TIME = request.GET["time"]
        if TIME == "":
            now = date.today().isoformat()
            TIME = now + "T00:00:00"
    except:
        now = date.today().isoformat()
        TIME = now + "T00:00:00"

    TIMES = TIME.split("/")

    for i in range(len(TIMES)):

        TIMES[i] = TIMES[i].replace("Z", "")
        if len(TIMES[i]) == 16:
            TIMES[i] = TIMES[i] + ":00"
        elif len(TIMES[i]) == 13:
            TIMES[i] = TIMES[i] + ":00:00"
        elif len(TIMES[i]) == 10:
            TIMES[i] = TIMES[i] + "T00:00:00"
    if len(TIMES) > 1:
        datestart = datetime.datetime.strptime(TIMES[0], "%Y-%m-%dT%H:%M:%S" )
        dateend = datetime.datetime.strptime(TIMES[1], "%Y-%m-%dT%H:%M:%S" )
        times = topology.variables['time'][:]
        time_units = topology.variables['time'].units
        datestart = round(netCDF4.date2num(datestart, units=time_units))
        dateend = round(netCDF4.date2num(dateend, units=time_units))
        time1 = bisect.bisect_right(times, datestart) - 1
        time2 = bisect.bisect_right(times, dateend) - 1

        if time1 == -1:
            time1 = 0
        if time2 == -1:
            time2 = len(times)

        time = range(time1, time2)
        if len(time) < 1:
            time = [len(times) - 1]
    else:
        datestart = datetime.datetime.strptime(TIMES[0], "%Y-%m-%dT%H:%M:%S" )
        times = topology.variables['time'][:]
        time_units = topology.variables['time'].units
        datestart = round(netCDF4.date2num(datestart, units=time_units))
        time1 = bisect.bisect_right(times, datestart) - 1
        if time1 == -1:
            time = [0]
        else:
            time = [time1-1]

    def getvar(nc, t, layer, var, ind):
        #nc = netCDF4.Dataset(url, 'r')
        if var == "time":
            #print var, t
            return nc.variables[var][t]
        else:
            # Expects 3d cell variables.
            if len(nc.variables[var].shape) == 3:
                return nc.variables[var][t, layer, ind]
            elif len(nc.variables[var].shape) == 2:
                return nc.variables[var][t, ind]
            elif len(nc.variables[var].shape) == 1:
                return nc.variables[var][ind]

    datasetnc = dataset.netcdf4_dataset()

    varis = deque()
    varis.append(getvar(topology, time, elevation, "time", index))
    if grid_type == 'ugrid':
        for var in QUERY_LAYERS:
            varis.append(getvar(datasetnc, time, elevation, var, index))
            try:
                units = datasetnc.variables[var].units
            except:
                units = ""
    else:
        """
        var1, var2 = cgrid.getvar(datasetnc, time, elevation, QUERY_LAYERS, index)
        varis.append(var1)
        if var2 is not None:
            varis.append(var2)
        """
        for var in QUERY_LAYERS:
            varis.append(cgrid.getvar(datasetnc, time, elevation, [var], index)[0])
        try:
            units = datasetnc.variables[QUERY_LAYERS[0]].units
        except:
            units = ""

    varis[0] = netCDF4.num2date(varis[0], units=time_units)
    X = numpy.asarray([var for var in varis])
    X = numpy.transpose(X)

    """
    if datasetnc.variables["time"].time_zone == "UTC":
        time_zone_offset = ZERO
    else:
        time_zone_offset = None
    """
    #print request.GET["INFO_FORMAT"]
    if request.GET["INFO_FORMAT"].lower() == "image/png":
        response = HttpResponse(content_type=request.GET["INFO_FORMAT"].lower())
        from matplotlib.figure import Figure
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(varis[0], varis[1])  # Actually make line plot
        tdelta = varis[0][-1]-varis[0][0]
        if tdelta.total_seconds()/3600. <= 36:
            if tdelta.total_seconds()/3600. <= 12:
                interval = 2
            elif tdelta.total_seconds()/3600. <= 24:
                interval = 4
            elif tdelta.total_seconds()/3600. <= 36:
                interval = 6
            ax.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
            ax.xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=interval))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y/%m/%d\n%H:%M'))
        if tdelta.total_seconds()/3600. <= 96:
            #if tdelta.total_seconds()/3600. <= 48:
            interval = 12
            #elif tdelta.total_seconds()/3600. <= 60:
            #    interval = 14
            #elif tdelta.total_seconds()/3600. <= 72:
            #    interval = 16
            ax.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
            ax.xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=interval))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y/%m/%d\n%H:%M'))
        if tdelta.total_seconds()/3600. <= 120:
            interval = 1
            ax.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
            ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=interval))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y/%m/%d'))
        if tdelta.total_seconds()/3600. <= 240:
            interval = 2
            ax.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
            ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=interval))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y/%m/%d'))
        ax.grid(True)
        ax.set_ylabel(QUERY_LAYERS[0] + "(" + units + ")")
        canvas = FigureCanvasAgg(fig)
        canvas.print_png(response)
    elif request.GET["INFO_FORMAT"].lower() == "application/json":
        import json
        response = HttpResponse("Response MIME Type application/json not supported at this time")
    elif request.GET["INFO_FORMAT"].lower() == "text/javascript":
        """
        http://docs.geoserver.org/latest/en/user/services/wms/reference.html#getfeatureinfo
        """
        import json
        callback = request.GET.get("info_format", "parseResponse")
        response = HttpResponse()
        output_dict = {}
        output_dict2 = {}
        output_dict["type"] = "Feature"
        output_dict["geometry"] = { "type" : "Point", "coordinates" : [float(selected_longitude), float(selected_latitude)] }
        varis[0] = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in varis[0]]
        output_dict2["time"] = {"units": "iso", "values": varis[0]}
        output_dict2["latitude"]  = { "units" : "degrees_north", "values" : float(selected_latitude) }
        output_dict2["longitude"] = { "units" : "degrees_east",  "values" : float(selected_longitude) }
        for i, var in enumerate(QUERY_LAYERS):  # TODO: use map to convert to floats
            varis[i+1] = list(varis[i+1])
            for q, v in enumerate(varis[i+1]):
                if numpy.isnan(v):
                    varis[i+1][q] = float("nan")
                else:
                    varis[i+1][q] = float(varis[i+1][q])
            output_dict2[var] = {"units": datasetnc.variables[var].units, "values": varis[i+1]}
        output_dict["properties"] = output_dict2
        output_str = callback + "(" + json.dumps(output_dict, indent=4, separators=(',', ': '), allow_nan=True) + ")"
        response.write(output_str)
    elif request.GET["INFO_FORMAT"].lower() == "text/csv":
        import csv
        buffer = StringIO()
        response = HttpResponse()
        #buffer.write(lat.__str__() + " , " + lon.__str__())
        #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f', newline="|")
        c = csv.writer(buffer)
        header = ["time"]
        header.append("latitude[degrees_north]")
        header.append("longitude[degrees_east]")
        for var in QUERY_LAYERS:
            header.append(var + "[" + datasetnc.variables[var].units + "]")
        c.writerow(header)
        for i, thistime in enumerate(varis[0]):
            thisline = [thistime.strftime("%Y-%m-%dT%H:%M:%SZ")]
            thisline.append(selected_latitude)
            thisline.append(selected_longitude)
            for k in range(1, len(varis)):
                if type(varis[k]) == numpy.ndarray or type(varis[k]) == numpy.ma.core.MaskedArray:
                    try:
                        thisline.append(varis[k][i])
                    except:
                        thisline.append(varis[k])
                else:  # If the variable is not changing with type, like bathy
                    thisline.append(varis[k])
            c.writerow(thisline)
        dat = buffer.getvalue()
        buffer.close()
        response.write(dat)
    else:
        response = HttpResponse("Response MIME Type %s not supported at this time" % request.GET["INFO_FORMAT"].lower())
    datasetnc.close()
    topology.close()
    return response


def demo(request):
    context = { 'datasets'  : Dataset.objects.all()}
    return render_to_response('wms/demo.html', context, context_instance=RequestContext(request))


from django.http import HttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect


def enhance_getmap_request(dataset, layer, request):
    gettemp = request.GET.copy()

    # 'time' parameter
    times = wms_handler.get_times(request)
    dimensions = wms_handler.get_dimensions(request)

    newgets = dict(
        starting=times.min,
        ending=times.max,
        time=wms_handler.get_time(request),
        crs=wms_handler.get_projection(request),
        bbox=wms_handler.get_bbox(request),
        wgs84_bbox=wms_handler.get_wgs84_bbox(request),
        colormap=wms_handler.get_colormap(request),
        colorscalerange=wms_handler.get_colorscalerange(request, layer.default_min, layer.default_max),
        elevation=wms_handler.get_elevation(request),
        width=dimensions.width,
        height=dimensions.height,
        image_type=wms_handler.get_imagetype(request)
    )
    gettemp.update(newgets)
    request.GET = gettemp

    # Check required parameters here and raise a ValueError if needed

    return request


def enhance_getlegendgraphic_request(dataset, layer, request):
    gettemp = request.GET.copy()

    dimensions = wms_handler.get_dimensions(request)

    newgets = dict(
        colorscalerange=wms_handler.get_colorscalerange(request, layer.default_min, layer.default_max),
        width=dimensions.width,
        height=dimensions.height,
        image_type=wms_handler.get_imagetype(request, parameter='style'),
        colormap=wms_handler.get_colormap(request, parameter='style'),
        format=wms_handler.get_format(request),
        showlabel=wms_handler.get_show_label(request),
        showvalues=wms_handler.get_show_values(request),
        units=wms_handler.get_units(request, layer.units),
        logscale=wms_handler.get_logscale(request),
        horizontal=wms_handler.get_horizontal(request),
        numcontours=wms_handler.get_num_contours(request)
    )
    gettemp.update(newgets)
    request.GET = gettemp
    return request


def enhance_getfeatureinfo_request(dataset, layer, request):
    gettemp = request.GET.copy()
    # 'time' parameter
    times = wms_handler.get_times(request)
    xy = wms_handler.get_xy(request)
    dimensions = wms_handler.get_dimensions(request)
    bbox = wms_handler.get_bbox(request)
    crs = wms_handler.get_projection(request)
    targets = wms_handler.get_gfi_positions(xy, bbox, crs, dimensions)

    newgets = dict(
        starting=times.min,
        ending=times.max,
        #x=xy.x,
        #y=xy.y,
        #bbox=bbox,
        latitude=targets.latitude,
        longitude=targets.longitude,
        #wgs84_bbox=wms_handler.get_wgs84_bbox(request),
        #width=dimensions.width,
        #height=dimensions.height,
        elevation=wms_handler.get_elevation(request),
        crs=crs,
        info_format=wms_handler.get_info_format(request)
    )
    gettemp.update(newgets)
    request.GET = gettemp
    return request


class DatasetShowView(View):

    def get(self, request, dataset):
        dataset = get_object_or_404(Dataset, slug=dataset)
        return TemplateResponse(request, 'wms/dataset.html', dict(dataset=dataset))


class DatasetListView(View):

    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            uri = request.POST['uri']
            name = request.POST['name']
            assert uri and name
        except (AssertionError, KeyError):
            return HttpResponse('URI and Name are required. Please try again.', status=500, reason="Could not process inputs", content_type="text/plain")

        klass = Dataset.identify(uri)
        if klass is not None:
            try:
                ds = klass.objects.create(uri=uri, name=name)
            except IntegrityError:
                return HttpResponse('Name is already taken, please choose another', status=500, reason="Could not process inputs", content_type="application/json")

            return HttpResponse(serializers.serialize('json', [ds]), status=201, content_type="application/json")
        else:
            return HttpResponse('Could not process the URI with any of the available Dataset types. Please check the URI and try again', status=500, reason="Could not process inputs", content_type="application/json")


class WmsView(View):

    def get(self, request, dataset):
        dataset = Dataset.objects.filter(slug=dataset).first()
        request = normalize_get_params(request)
        reqtype = request.GET['request']

        # This calls the passed in 'request' method on a Dataset and returns the response
        try:
            if reqtype.lower() == 'getcapabilities':
                return TemplateResponse(request, 'wms/getcapabilities.xml', dict(dataset=dataset, server=Server.objects.first()), content_type='application/xml')
            else:
                layer = get_layer_from_request(dataset, request)
                if not layer:
                    raise ValueError('Could not find a layer named "{}"'.format(request.GET.get('layers')))
                if reqtype.lower() == 'getmap':
                    request = enhance_getmap_request(dataset, layer, request)
                elif reqtype.lower() == 'getlegendgraphic':
                    request = enhance_getlegendgraphic_request(dataset, layer, request)
                elif reqtype.lower() == 'getfeatureinfo':
                    request = enhance_getfeatureinfo_request(dataset, layer, request)
                try:
                    response = getattr(dataset, reqtype.lower())(layer, request)
                except AttributeError as e:
                    logger.exception(e)
                    return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
                except NotImplementedError as e:
                    return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
                # Test formats, etc. before returning?
                return response
        except ValueError as e:
            logger.exception(str(e))
            return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
        except AttributeError as e:
            logger.exception(str(e))
            return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
        except NotImplementedError as e:
            logger.exception(str(e))
            return HttpResponse('"{}" is not implemented for a {}'.format(reqtype, dataset.__class__.__name__), status=500, reason="Could not process inputs", content_type="application/json")
