'''
Created on Sep 1, 2011

@author: ACrosby
'''
# Create your views here.
from django.http import HttpResponse
import numpy
import netCDF4
from pywms.wms.models import Dataset, Server
from django.contrib.sites.models import Site
import matplotlib
matplotlib.use("Agg")
from mpl_toolkits.basemap import Basemap
import datetime
from collections import deque
from StringIO import StringIO # will be deprecated in Python3, use io.byteIO instead
import math
import pywms.server_local_config as config
from matplotlib.backends.backend_agg import FigureCanvasAgg
import gc
import time as timeobj
import bisect
import pywms.grid_init_script as grid
import os
import matplotlib.pyplot as plt
from matplotlib.pylab import get_cmap
            
try:
    import cPickle as pickle
except ImportError:
    import Pickle as pickle
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET



def testdb(request):
    print dir(Dataset.objects.get(name='necofs'))
    return HttpResponse(str(Dataset.objects.get(name='necofs').uri), content_type='text')
    
def index(request):
    import django.shortcuts as dshorts
    context = { "datasets":Dataset.objects.values()}
    return dshorts.render_to_response('index.html', context)

def openlayers (request, filepath):
    f = open(os.path.join(config.staticspath, "openlayers", filepath))
    text = f.read()
    f.close()
    #return dshorts.render_to_response(text, dict1)
    return HttpResponse(text, content_type='text')

def static (request, filepath):
    f = open(os.path.join(config.staticspath, filepath))
    text = f.read()
    f.close()
    #return dshorts.render_to_response(text, dict1)
    return HttpResponse(text, content_type='text/css')
    
def wmstest (request):
    import multiprocessing
    #p = multiprocessing.Process(target=grid.check_topology_age)
    #p.daemon = True
    #p.start()
    grid.check_topology_age()
    import django.shortcuts as dshorts
    from django.template import Context, Template
    f = open(os.path.join(config.staticspath, "wms_openlayers_test.html"))
    text = f.read()
    f.close()
    sites = Site.objects.values()
    dict1 = Context({ 'localsite':sites[0]['domain'],
                      'datasets':Dataset.objects.values()})
    #return dshorts.render_to_response(text, dict1)
    return HttpResponse(Template(text).render(dict1))

def documentation (request):
    #jobsarray = grid.check_topology_age()
    import django.shortcuts as dshorts
    import os
    #import pywms.server_local_config as config
    f = open(os.path.join(config.fullpath_to_wms, "README.md"))
    text = f.read()
    dict1 = { "textfile":text}
    return dshorts.render_to_response('docs.html', dict1)
    
def crossdomain (request):
    f = open(config.staticspath + "crossdomain.xml")
    test = f.read()
    response = HttpResponse(content_type="text/xml")
    response.write(test)
    return response

def wms (request, dataset):
    #jobsarray = grid.check_topology_age()
    try:
        reqtype = request.GET['REQUEST']
    except:
        reqtype = request.GET['request']
    if reqtype.lower() == 'getmap':
        import pywms.wms.wms_handler as wms
        handler = wms.wms_handler(request)
        action_request = handler.make_action_request(request)
        if action_request is not None:
            response = fvDo(action_request, dataset)
        else:
            response = HttpResponse()
    elif reqtype.lower() == 'getfeatureinfo':
        response =  getFeatureInfo(request, dataset)
    elif reqtype.lower() == 'getlegendgraphic':
        response =  getLegendGraphic(request, dataset)
    elif reqtype.lower() == 'getcapabilities':
        response = getCapabilities(request, dataset)
        #response = HttpResponse()
    return response

def getCapabilities(request, dataset):
    """
    get capabilities document based on this getcaps:
    
    
    http://coastmap.com/ecop/wms.aspx?service=WMS&version=1.1.1&request=getcapabilities

    """
    # Create the object to be encoded to xml later
    root = ET.Element('WMT_MS_Capabilities')
    root.attrib["version"] = "1.1.1"#request.GET["version"]
    href = "http://" + Site.objects.values()[0]['domain'] + "/wms/" + dataset + "/?"

    # Plug into your generic implentation of sciwms template
    # will have to pull these fields out of the database directly 
    # to ensure uptodate
    service = ET.SubElement(root, 'Service')
    
    servermetadata = Server.objects.values()[0]
    ET.SubElement(service, "Name").text = "OGC:WMS"
    ET.SubElement(service, "Title").text = servermetadata["title"]
    ET.SubElement(service, "Abstract").text = servermetadata["abstract"]
    keywordlist = ET.SubElement(service, "KeywordList")
    keywords       = servermetadata["keywords"].split(",")
    for keyword in keywords:
        ET.SubElement(keywordlist, "Keyword").text = keyword
    onlineresource = ET.SubElement(service, "OnlineResource")
    onlineresource.attrib["xlink:type"] = "simple"
    onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
    #Contact Information
    contactinformation = ET.SubElement(service, "ContactInformation")
    primarycontact = ET.SubElement(contactinformation, "ContactPersonPrimary")
    ET.SubElement(primarycontact, "ContactPerson").text = servermetadata["contact_person"]
    ET.SubElement(primarycontact, "ContactOrganization").text = servermetadata["contact_organization"]
    ET.SubElement(contactinformation, "ContactPosition").text = servermetadata["contact_position"]
    contactaddress = ET.SubElement(contactinformation, "ContactAddress")
    ET.SubElement(contactaddress, "AddressType").text = "postal"
    ET.SubElement(contactaddress, "Address").text = servermetadata["contact_street_address"]
    ET.SubElement(contactaddress, "City").text = servermetadata["contact_city_address"]
    ET.SubElement(contactaddress, "StateOrProvince").text = servermetadata["contact_state_address"]
    ET.SubElement(contactaddress, "PostCode").text = servermetadata['contact_code_address']
    ET.SubElement(contactaddress, "Country").text = servermetadata['contact_country_address']
    ET.SubElement(contactinformation, "ContactVoiceTelephone").text = servermetadata['contact_telephone']
    ET.SubElement(contactinformation, "ContactElectronicMailAddress").text = servermetadata['contact_email']
    
    # Capability elements (hardcoded)
    capability = ET.SubElement(root, "Capability")
    request = ET.SubElement(capability, "Request")
    # GetCaps
    getcaps = ET.SubElement(request, "GetCapabilities")
    ET.SubElement(getcaps, "Format").text = "application/vnd.ogc.wms_xml"
    ET.SubElement(getcaps, "Format").text = "text/xml"
    getcaps_dcptype = ET.SubElement(getcaps, "DCPType")
    getcaps_http = ET.SubElement(getcaps_dcptype, "HTTP")
    getcaps_get = ET.SubElement(getcaps_http, "Get")
    getcaps_onlineresource = ET.SubElement(getcaps_get, "OnlineResource")
    getcaps_onlineresource.attrib["xlink:type"] = "simple"
    getcaps_onlineresource.attrib["xlink:href"] = href
    getcaps_onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
    # GetMap
    getmap = ET.SubElement(request, "GetMap")
    ET.SubElement(getmap, "Format").text = "image/png"
    #ET.SubElement(getmap, "Format").text = "text/csv"
    #ET.SubElement(getmap, "Format").text = "application/netcdf"
    #ET.SubElement(getmap, "Format").text = "application/matlab-mat"
    #ET.SubElement(getmap, "Format").text = "application/x-zip-esrishp"
    getmap_dcptype = ET.SubElement(getmap, "DCPType")
    getmap_http = ET.SubElement(getmap_dcptype, "HTTP")
    getmap_get = ET.SubElement(getmap_http, "Get")
    getmap_onlineresource = ET.SubElement(getmap_get, "OnlineResource")
    getmap_onlineresource.attrib["xlink:type"] = "simple"
    getmap_onlineresource.attrib["xlink:href"] = href
    getmap_onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
    # GetFeatureInfo
    gfi = ET.SubElement(request, "GetFeatureInfo")
    ET.SubElement(gfi, "Format").text = "image/png"
    ET.SubElement(getmap, "Format").text = "text/csv"
    #ET.SubElement(getmap, "Format").text = "application/netcdf"
    #ET.SubElement(getmap, "Format").text = "application/matlab-mat"
    #ET.SubElement(getmap, "Format").text = "application/x-zip-esrishp"
    gfi_dcptype = ET.SubElement(gfi, "DCPType")
    gfi_http = ET.SubElement(gfi_dcptype, "HTTP")
    gfi_get = ET.SubElement(gfi_http, "Get")
    gfi_onlineresource = ET.SubElement(gfi_get, "OnlineResource")
    gfi_onlineresource.attrib["xlink:type"] = "simple"
    gfi_onlineresource.attrib["xlink:href"] = href
    gfi_onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
    # GetLegendGraphic
    getlegend = ET.SubElement(request, "GetLegendGraphic")
    ET.SubElement(getlegend, "Format").text = "image/png"
    getlegend_dcptype = ET.SubElement(getlegend, "DCPType")
    getlegend_http = ET.SubElement(getlegend_dcptype, "HTTP")
    getlegend_get = ET.SubElement(getlegend_http, "Get")
    getlegend_onlineresource = ET.SubElement(getlegend_get, "OnlineResource")
    getlegend_onlineresource.attrib["xlink:type"] = "simple"
    getlegend_onlineresource.attrib["xlink:href"] = href
    getlegend_onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
    #Exception
    exception = ET.SubElement(capability, "Exception")
    ET.SubElement(exception, "Format").text = "text/html"
   
    # Pull layer description directly from database
    onlineresource.attrib["href"] = href
    # Layers
    layer = ET.SubElement(capability, "Layer") 
    ET.SubElement(layer, "Title").text =  Dataset.objects.get(name=dataset).title
    ET.SubElement(layer, "Abstract").text =  Dataset.objects.get(name=dataset).abstract
    ET.SubElement(layer, "SRS").text =  "EPSG:3857"
    ET.SubElement(layer, "SRS").text =  "MERCATOR"
    nc = netCDF4.Dataset(Dataset.objects.get(name=dataset).uri)
    topology = netCDF4.Dataset(os.path.join(config.topologypath, dataset + '.nc'))
    for variable in nc.variables.keys():
        try:
            location = nc.variables[variable].location
        except:
            location = "node"
        if location == "face":
            location = "cell"
        try:
            nc.variables[variable].location
            layer1 = ET.SubElement(layer, "Layer")
            layer1.attrib["queryable"] = "1"
            layer1.attrib["opaque"] = "0"
            ET.SubElement(layer1, "Name").text = variable
            try:
                try:
                    ET.SubElement(layer1, "Title").text = nc.variables[variable].standard_name
                except:
                    ET.SubElement(layer1, "Title").text = nc.variables[variable].long_name
            except:
                ET.SubElement(layer1, "Title").text = variable
            try:
                try:
                    ET.SubElement(layer1, "Abstract").text = nc.variables[variable].summary
                except:
                    ET.SubElement(layer1, "Abstract").text = nc.variables[variable].long_name
            except:
                ET.SubElement(layer1, "Abstract").text = variable
            ET.SubElement(layer1, "SRS").text = "EPSG:4326"
            llbbox = ET.SubElement(layer1, "LatLonBoundingBox")
            llbbox.attrib["minx"] = "-180"
            llbbox.attrib["miny"] = "-90"
            llbbox.attrib["maxx"] = "180"
            llbbox.attrib["maxy"] = "90"
            llbbox = ET.SubElement(layer1, "BoundingBox")
            llbbox.attrib["SRS"] = "EPSG:4326"
            llbbox.attrib["minx"] = "-180"
            llbbox.attrib["miny"] = "-90"
            llbbox.attrib["maxx"] = "180"
            llbbox.attrib["maxy"] = "90"
            if nc.variables[variable].ndim > 2:
                try:
                    ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables["siglay"].shape[0])).replace("[","").replace("]","")
                except:
                    ET.SubElement(layer1, "DepthLayers").text = ""
                try:
                    if nc.variables["siglay"].positive.lower() == "up":
                        ET.SubElement(layer1, "DepthDirection").text = "Down"
                    elif nc.variables["siglay"].positive.lower() == "down":
                        ET.SubElement(layer1, "DepthDirection").text = "Up"
                    else:
                        ET.SubElement(layer1, "DepthDirection").text = ""
                except:
                    ET.SubElement(layer1, "DepthDirection").text = ""
            else:
                ET.SubElement(layer1, "DepthLayers").text = "0"
                ET.SubElement(layer1, "DepthDirection").text = "Down"
            for style in ["filledcontours", "contours", "pcolor", "facets"]:
                style_code = style + "_average_jet_None_None_" + location + "_False"
                style = ET.SubElement(layer1, "Style")
                ET.SubElement(style, "Name").text = style_code
                ET.SubElement(style, "Title").text = style_code
                ET.SubElement(style, "Abstract").text = "http://" + Site.objects.values()[0]['domain'] + "/doc"
                legendurl = ET.SubElement(style, "LegendURL")
                legendurl.attrib["width"] = "50"
                legendurl.attrib["height"] = "80"
                ET.SubElement(legendurl, "Format").text = "image/png"
                #legend_onlineresource = ET.SubElement(legendurl, "OnlineResource")
                #legend_onlineresource.attrib["xlink:type"] = "simple"
                #legend_onlineresource.attrib["xlink:href"] = href
                #legend_onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
            if variable == "u" or variable == "u-vel" or variable == "ua":
                style_code = "vectors_average_jet_None_None_" + location + "_False"
                if variable == "u":
                    layername = "u,v"
                elif variable == "u-vel":
                    layername = "u-vel,v-vel"
                elif variable == "ua":
                    layername = "ua,va"
                try:
                    location = nc.variables[variable].location
                except:
                    location = "node"
                if location == "face":
                    location = "cell"
                layer1 = ET.SubElement(layer, "Layer")
                layer1.attrib["queryable"] = "1"
                layer1.attrib["opaque"] = "0"
                ET.SubElement(layer1, "Name").text = layername
                ET.SubElement(layer1, "Title").text = "current velocity (u,v)"
                ET.SubElement(layer1, "Abstract").text = "Magnitude of current velocity from u and v components"
                ET.SubElement(layer1, "SRS").text = "EPSG:4326"
                llbbox = ET.SubElement(layer1, "LatLonBoundingBox")
                llbbox.attrib["minx"] = "-180"
                llbbox.attrib["miny"] = "-90"
                llbbox.attrib["maxx"] = "180"
                llbbox.attrib["maxy"] = "90"
                llbbox = ET.SubElement(layer1, "BoundingBox")
                llbbox.attrib["SRS"] = "EPSG:4326"
                llbbox.attrib["minx"] = "-180"
                llbbox.attrib["miny"] = "-90"
                llbbox.attrib["maxx"] = "180"
                llbbox.attrib["maxy"] = "90"
                time_dimension = ET.SubElement(layer1, "Dimension")
                time_dimension.attrib["name"] = "time"
                time_dimension.attrib["time"] = "ISO8601"
                time_extent = ET.SubElement(layer1, "Extent")
                time_extent.attrib["name"] = "time"
                elev_extent = ET.SubElement(layer1, "Extent")
                elev_extent.attrib["name"] = "elevation"
                elev_extent.attrib["default"] = "0"
                try:
                    units = topology.variables["time"].units
                    time_extent.text = netCDF4.num2date(topology.variables["time"][0],units).isoformat('T') + "Z/" + netCDF4.num2date(topology.variables["time"][-1],units).isoformat('T') + "Z"
                except:
                    time_extent.text = str(topology.variables["time"][0]) + "/" + str(topology.variables["time"][-1])
                if nc.variables[variable].ndim > 2:
                    try:
                        ET.SubElement(layer1, "DepthLayers").text =  str(range(nc.variables["siglay"].shape[0])).replace("[","").replace("]","")
                        elev_extent.text = str(range(nc.variables["siglay"].shape[0])).replace("[","").replace("]","")
                    except:
                        ET.SubElement(layer1, "DepthLayers").text = ""
                    try:
                        if nc.variables["siglay"].positive.lower() == "up":
                            ET.SubElement(layer1, "DepthDirection").text = "Down"
                        elif nc.variables["siglay"].positive.lower() == "down":
                            ET.SubElement(layer1, "DepthDirection").text = "Up"
                        else:
                            ET.SubElement(layer1, "DepthDirection").text = ""
                    except:
                        ET.SubElement(layer1, "DepthDirection").text = ""
                else:
                    ET.SubElement(layer1, "DepthLayers").text = "0"
                    ET.SubElement(layer1, "DepthDirection").text = "Down"
                style = ET.SubElement(layer1, "Style")
                ET.SubElement(style, "Name").text = style_code
                ET.SubElement(style, "Title").text = style_code
                ET.SubElement(style, "Abstract").text = "http://" + Site.objects.values()[0]['domain'] + "/doc"
                legendurl = ET.SubElement(style, "LegendURL")
                legendurl.attrib["width"] = "50"
                legendurl.attrib["height"] = "80"
                ET.SubElement(legendurl, "Format").text = "image/png"
                #legend_onlineresource = ET.SubElement(legendurl, "OnlineResource")
                #legend_onlineresource.attrib["xlink:type"] = "simple"
                #legend_onlineresource.attrib["xlink:href"] = href
                #legend_onlineresource.attrib["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
        except:
            pass
    tree = ET.ElementTree(root)
    # Return the response
    response = HttpResponse(content_type="text/plain")
    response.write(r'<?xml version="1.0" encoding="utf-8"?>')
    tree.write(response)
    return response
    
def getLegendGraphic(request, dataset):
    """
    Parse parameters from request that looks like this:
    
    http://webserver.smast.umassd.edu:8000/wms/NecofsWave?
    ELEVATION=1
    &LAYERS=hs
    &TRANSPARENT=TRUE
    &STYLES=facets_average_jet_0_0.5_node_False
    &SERVICE=WMS
    &VERSION=1.1.1
    &REQUEST=GetLegendGraphic
    &FORMAT=image%2Fpng
    &TIME=2012-06-20T18%3A00%3A00
    &SRS=EPSG%3A3857
    &LAYER=hs
    """
    styles = request.GET["STYLES"].split("_")
    try:
        climits = (float(styles[3]), float(styles[4]))
    except:
        climits = (None, None)
    datestart = datetime.datetime.strptime(request.GET["TIME"], "%Y-%m-%dT%H:%M:%S" )
    #level = request.GET["ELEVATION"]
    #level = level.split(",")
    #for i,l in enumerate(level):
    #    level[i] = int(l)-1
    variables = request.GET["LAYER"].split(",")
    topology_type = styles[5]
    plot_type = styles[0]
    #magnitudebool = styles[6]
    colormap = styles[2]
    
    # direct the service to the dataset
    # make changes to server_local_config.py 
    if config.localdataset:
        url = config.localpath[dataset]
    else:
        url = Dataset.objects.get(name=dataset).uri
    nc = netCDF4.Dataset(url)
    
    
    """
    Create figure and axes for small legend image
    """
    from matplotlib.figure import Figure
    fig = Figure(dpi=100., facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figwidth(1*1.3)
    fig.set_figheight(1.5*1.3)
                            
    """
    Create the colorbar or legend and add to axis
    """
    if climits[0] is None or climits[1] is None: # TODO: NOT SUPPORTED RESPONSE
            #going to have to get the data here to figure out bounds
            #need elevation, bbox, time, magnitudebool
            CNorm=None
            ax = fig.add_axes([0, 0, 1, 1])
            ax.grid(False)
            ax.text(.5,.5, 'Error: No Legend\navailable for\nautoscaled\ncolor styles!', ha='center', va='center', transform=ax.transAxes, fontsize=8)
    elif plot_type not in ["contours", "filledcontours",]:
        #use limits described by the style
        ax = fig.add_axes([.01, .05, .2, .8])#, xticks=[], yticks=[])
        CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                            vmax=climits[1],
                                            clip=False,
                                            )
        cb = matplotlib.colorbar.ColorbarBase(ax,
                                              cmap=colormap,
                                              norm=CNorm,
                                              orientation='vertical',
                                              )
        cb.set_label(nc.variables[variables[0]].units)
    else:#plot type somekind of contour
        if plot_type == "contours":
            #this should perhaps be a legend...
            #ax = fig.add_axes([0,0,1,1])
            fig_proxy = Figure(frameon=False, facecolor='none', edgecolor='none')
            ax_proxy = fig_proxy.add_axes([0, 0, 1, 1])
            CNorm = matplotlib.colors.Normalize(vmin=climits[0],vmax=climits[1],clip=True)
            levs = numpy.arange(0, 12)*(climits[1]-climits[0])/10
            
            x, y = numpy.meshgrid(numpy.arange(10),numpy.arange(10))
            cs = ax_proxy.contourf(x, y, x, levels=levs, norm=CNorm, cmap=get_cmap(colormap))

            proxy = [plt.Rectangle((0,0),0,0,fc = pc.get_facecolor()[0]) 
                for pc in cs.collections]

            fig.legend(proxy, levs,
                       #bbox_to_anchor = (0, 0, 1, 1), 
                       #bbox_transform = fig.transFigure, 
                       loc = 6,
                       title = nc.variables[variables[0]].units, 
                       prop = {'size':8},
                       frameon = False,
                       )
        elif plot_type == "filledcontours":
            #this should perhaps be a legend...
            #ax = fig.add_axes([0,0,1,1])
            fig_proxy = Figure(frameon=False, facecolor='none', edgecolor='none')
            ax_proxy = fig_proxy.add_axes([0, 0, 1, 1])
            CNorm = matplotlib.colors.Normalize(vmin=climits[0],vmax=climits[1],clip=False,)
            levs = numpy.arange(1, 12)*(climits[1]-(climits[0]))/10
            levs = numpy.hstack(([-99999], levs, [99999]))
            
            x, y = numpy.meshgrid(numpy.arange(10),numpy.arange(10))
            cs = ax_proxy.contourf(x, y, x, levels=levs, norm=CNorm, cmap=get_cmap(colormap))

            proxy = [plt.Rectangle((0,0),0,0,fc = pc.get_facecolor()[0]) 
                for pc in cs.collections]
 
            levels = []
            for i, value in enumerate(levs):
                #if i == 0:
                #    levels[i] = "<" + str(value)
                if i == len(levs)-1:
                    levels.append(">" + str(value))
                else:
                    levels.append(str(value) + "-" + str(levs[i+1]))
            print levels, levs
            fig.legend(proxy, levels,
                       #bbox_to_anchor = (0, 0, 1, 1), 
                       #bbox_transform = fig.transFigure, 
                       loc = 6,
                       title = nc.variables[variables[0]].units, 
                       prop = {'size':6},
                       frameon = False,
                       )
    
    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
        
        
def getFeatureInfo(request, dataset):
    """
     /wms/GOM3/?ELEVATION=1&LAYERS=temp&FORMAT=image/png&TRANSPARENT=TRUE&STYLES=facets_average_jet_0_32_node_False&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&SRS=EPSG:3857&BBOX=-7949675.196111,5078194.822174,-7934884.63114,5088628.476533&X=387&Y=196&INFO_FORMAT=text/csv&WIDTH=774&HEIGHT=546&QUERY_LAYERS=salinity&TIME=2012-08-14T00:00:00/2012-08-16T00:00:00
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

    X = float(request.GET['X'])
    Y = float(request.GET['Y'])
    #print X, Y
    #VERSION = 
    box = request.GET["BBOX"]
    box = box.split(",")
    latmin = float(box[1])
    latmax = float(box[3])
    lonmin = float(box[0])
    lonmax = float(box[2])
    height = float(request.GET["HEIGHT"])
    width = float(request.GET["WIDTH"])
    styles = request.GET["STYLES"].split(",")[0].split("_")
    #print styles
    #LAYERS = request.GET['LAYERS']
    #FORMAT =  request.GET['FORMAT']
    #TRANSPARENT = 
    QUERY_LAYERS = request.GET['QUERY_LAYERS'].split(",")
    INFO_FORMAT = "text/plain" # request.GET['INFO_FORMAT']
    projection = 'merc'#request.GET['SRS']
    TIME = request.GET['TIME']
    elevation = [int(request.GET['ELEVATION'])]
    #print elevation
    
    from mpl_toolkits.basemap import pyproj
    mi = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs ")
    lon, lat = mi(lonmin+(lonmax-lonmin)*(X/width),
                            latmin+(latmax-latmin)*(Y/height),
                            inverse=True)
    lonmin, latmin = mi(lonmin, latmin, inverse=True)
    lonmax, latmax = mi(lonmax, latmax, inverse=True)

    #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
    #            urcrnrlon=lonmax, urcrnrlat=latmax,
    #            projection=projection,                             
    #            resolution=None,
    #            lat_ts = 0.0,
    #            suppress_ticks=True)
    
    topology = netCDF4.Dataset(os.path.join(config.topologypath, dataset + '.nc'))

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
        time_units = topology.variables['time'].units
    else:
        TIMES = TIME.split("/")
        if len(TIMES) > 1:
            datestart = datetime.datetime.strptime(TIMES[0], "%Y-%m-%dT%H:%M:%S" )
            dateend = datetime.datetime.strptime(TIMES[1], "%Y-%m-%dT%H:%M:%S" )
            times = topology.variables['time'][:]
            time_units = topology.variables['time'].units
            datestart = netCDF4.date2num(datestart, units=time_units)
            dateend = netCDF4.date2num(dateend, units=time_units)
            time1 = bisect.bisect_right(times, datestart) - 1
            time2 = bisect.bisect_right(times, dateend) - 1
            if time1 == -1:
                time1 = 0
            if time2 == -1:
                time2 = len(times)
            time = range(time1, time2)

        else:
            datestart = datetime.datetime.strptime(TIMES[0], "%Y-%m-%dT%H:%M:%S" )
            times = topology.variables['time'][:]
            time_units = topology.variables['time'].units
            datestart = netCDF4.date2num(datestart, units=time_units)
            time1 = bisect.bisect_right(times, datestart) - 1
            if time1 == -1:
                time = [0]
            else:
                time = [time1]
    
    pvar = deque()
    def getvar(nc, t, layer, var, ind):
        #nc = netCDF4.Dataset(url, 'r')
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
        url = Dataset.objects.get(name=dataset).uri
    datasetnc = netCDF4.Dataset(url)
   
    varis = deque()
    varis.append(getvar(datasetnc, time, elevation, "time", index))
    for var in QUERY_LAYERS:
        varis.append(getvar(datasetnc, time, elevation, var, index))
        try:
            units = datasetnc.variables[var].units
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
        import matplotlib.dates as mdates
        response = HttpResponse(content_type=request.GET["INFO_FORMAT"].lower())
        from matplotlib.figure import Figure
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(varis[0],varis[1]) # Actually make line plot
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
    else: 
        import csv
        response = HttpResponse()
        buffer = StringIO()
        #buffer.write(lat.__str__() + " , " + lon.__str__())
        #numpy.savetxt(buffer, X, delimiter=",", fmt='%10.5f', newline="|")
        c = csv.writer(buffer)
        header = ["time"]
        for var in QUERY_LAYERS:
            header.append(var + "[" + datasetnc.variables[var].units + "]")
        c.writerow(header)
        for i, thistime in enumerate(varis[0]):
            thisline = [thistime.strftime("%Y%m%dT%H%M%SZ")]
            for k in range(1, len(varis)):
                thisline.append(varis[k][i])
            c.writerow(thisline)         
        dat = buffer.getvalue()
        buffer.close()
        response.write(dat)
        topology.close()
    return response

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
        url = Dataset.objects.get(name=dataset).uri
        

    width = float(request.GET["width"])
    height = float(request.GET["height"])
    latmax = float(request.GET["latmax"])
    latmin = float(request.GET["latmin"])
    lonmax = float(request.GET["lonmax"])
    lonmin = float(request.GET["lonmin"])
    
    from mpl_toolkits.basemap import pyproj
    mi = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs ")
    lonmin, latmin = mi(lonmin, latmin, inverse=True)
    lonmax, latmax = mi(lonmax, latmax, inverse=True)
    #print "ll", lonmin, latmin, "ur", lonmax, latmax

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
    
    magnitude = request.GET["magnitude"]
        

    topology_type = request.GET["topologytype"]
        
    variables = request.GET["variables"].split(",")
    continuous = False
    
    if "kml" in actions:
        pass
    else:
        
        topology = netCDF4.Dataset(os.path.join(config.topologypath, dataset + '.nc'))
        datasetnc = netCDF4.Dataset(url)

        if latmax != latmin:
            if lonmin > lonmax:
                lonmax = lonmax + 360
                continuous = True
                lon = topology.variables['lonc'][:]
                wher = numpy.where(lon<lonmin)
                lon[wher] = lon[wher] + 360
            else:
                lon = topology.variables['lonc'][:]
            lat = topology.variables['latc'][:]
            index = numpy.asarray(numpy.where(
                (lat <= latmax+.18) & (lat >= latmin-.18) &
                (lon <= lonmax+.18) & (lon >= lonmin-.18),)).squeeze()
            lat = lat[index]
            lon = lon[index]
            
        else:
            pass
        print "index", len(index)
        if len(index) > 0:
            #job_server = pp.Server(4, ppservers=()) 
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
                
                #nv = topology.variables['nv'][:,index].T-1
                nvtemp = topology.variables['nv'][:,:]#.T-1
                nv = nvtemp[:,index].T-1
                latn = topology.variables['lat'][:]
                lonn = topology.variables['lon'][:]
                if topology_type.lower() == "node":
                    index = range(len(latn))
                if continuous is True:
                    if lonmin < 0:
                        lonn[numpy.where(lonn > 0)] = lonn[numpy.where(lonn > 0)] - 360
                        lonn[numpy.where(lonn < lonmax-359)] = lonn[numpy.where(lonn < lonmax-359)] + 360
                    else:
                        lonn[numpy.where(lonn < lonmax-359)] = lonn[numpy.where(lonn < lonmax-359)] + 360
                uu = numpy.unique(nv)
                print numpy.min(uu), numpy.max(uu)
            else:
                nv = None

            datestart = datetime.datetime.strptime( datestart, "%Y-%m-%dT%H:%M:%S" )
            #dateend = datetime.datetime.strptime( dateend, "%Y-%m-%dT%H:%M:%S" )
            times = topology.variables['time'][:]
            datestart = netCDF4.date2num(datestart,
                units=topology.variables['time'].units)
            #dateend = date2num(dateend, units=times.units)
            time = bisect.bisect_right(times, datestart) - 1
            if config.localdataset:
                time = [1]
            elif time == -1:
                time = [0]
            else:
                time = [time]
            
            print time
            
            #pvar = deque()
            def getvar(nc, t, layer, var):
                #nc = netCDF4.Dataset(url, 'r')
                # Expects 3d cell variables.
                if len(nc.variables[var].shape) == 3:
                    return nc.variables[var][t, layer[0], :]
                elif len(nc.variables[var].shape) == 2:
                    return nc.variables[var][t, :]
                elif len(nc.variables[var].shape) == 1:
                    return nc.variables[var][:]

            t = time

            var1 = getvar(datasetnc, t, layer, variables[0])
            if len(variables) > 1:
                var2 = getvar(datasetnc, t, layer, variables[1])

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

                    m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                            #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                            resolution=None,
                            lat_ts = 0.0,
                            suppress_ticks=True)
                            
                    m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])

                    if "regrid" in actions:
                        """
                        import pywms.wms.regrid as regrid
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
                            if topology_type.lower() == 'cell':
                                pass
                            else:
                                lon, lat = lonn, latn
                                
                            #print "points ll", numpy.min(lon), numpy.min(lat), "ur", numpy.max(lon), numpy.max(lat)
                            lon, lat = m(lon, lat)

                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                                vmax=climits[1],
                                                                clip=True,
                                                                )
                                       
                            if magnitude == "True":
                                arrowsize = None
                            elif magnitude == "False":
                                arrowsize = 2.
                            elif magnitude == "None":
                                arrowsize = None
                            else:
                                arrowsize = float(magnitude)
                                
                            
                            if topology_type.lower() == 'node':
                                n = numpy.unique(nv)
                                m.quiver(lon[n], lat[n], var1[n], var2[n], mag[n], 
                                    pivot='mid',
                                    units='xy', #xy
                                    cmap=colormap,
                                    norm=CNorm,
                                    minlength=.5,
                                    scale=arrowsize,
                                    scale_units='inches',
                                    )
                            else:
                                m.quiver(lon, lat, var1, var2, mag, 
                                    pivot='mid',
                                    units='xy', #xy
                                    cmap=colormap,
                                    norm=CNorm,
                                    minlength=.5,
                                    scale=arrowsize,
                                    scale_units='inches',
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
                            if topology_type.lower() == 'cell':
                                pass
                            else:
                                lon, lat = lonn, latn

                            lon, lat = m(lon, lat)
                             
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
                            if topology_type.lower() == 'node':
                                n = numpy.unique(nv)
                                m.ax.barbs(lon[n], lat[n], var1[n], var2[n], mag[n],
                                    length=7.,
                                    pivot='middle',
                                    barb_increments=dict(half=full/2., full=full, flag=flag),
                                    #units='xy',
                                    cmap=colormap,
                                    norm=CNorm,
                                    #clim=climits,
                                    linewidth=1.7,
                                    sizes=dict(emptybarb=0.2, spacing=0.14, height=0.5),
                                    #antialiased=True,
                                    )
                            else:
                                m.ax.barbs(lon, lat, var1, var2, mag,
                                    length=7.,
                                    pivot='middle',
                                    barb_increments=dict(half=full/2., full=full, flag=flag),
                                    #units='xy',
                                    cmap=colormap,
                                    norm=CNorm,
                                    #clim=climits,
                                    linewidth=1.7,
                                    sizes=dict(emptybarb=0.2, spacing=.14, height=0.5),
                                    #antialiased=True,
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
                                if magnitude == "True":
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
                            if topology_type.lower() == 'cell':
                                #if continuous is True:
                                #    lon[np.where(lon < lonmin)] = lon[np.where(lon < lonmin)] + 360
                            
                                lon, lat = m(lon, lat)
                                trid = Tri.Triangulation(lon, lat)
                                #mask = []
                                #for triangs in trid.triangles:
                                #    mask.append(m.is_land(
                                #    lon[triangs].mean(),
                                #    lat[triangs].mean()))
                                #trid.set_mask(mask)
                                m.ax.tricontour(trid, mag, norm=CNorm, levels=levs, antialiased=True, linewidth=2)
                                
                                import shapely.geometry
                                import matplotlib.patches as patches

                                f = open(os.path.join(config.topologypath, dataset + '.domain'))
                                domain = pickle.load(f)
                                f.close()
                                if continuous is True:
                                    if lonmin < 0:
                                        #x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                        #x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 0, latmax),
                                                                             shapely.geometry.box(0, latmin, lonmax, latmax)))
                                    else:
                                        box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 180, latmax),
                                                                             shapely.geometry.box(-180, latmin, lonmax-360, latmax)))
                                else:
                                    box = shapely.geometry.box(lonmin, latmin, lonmax, latmax)
                                
                                domain = domain.intersection(box)
                                
                                buffer = StringIO()
                            
                                lonmax1, latmax1 = m(lonmax, latmax)
                                lonmin1, latmin1 = m(lonmin, latmin)
                                m.ax.set_xlim(lonmin1, lonmax1)
                                m.ax.set_ylim(latmin1, latmax1)
                                m.ax.set_frame_on(False)
                                m.ax.set_clip_on(False)
                                m.ax.set_position([0,0,1,1])
                    
                                canvas = FigureCanvasAgg(fig)
                                canvas.print_png("temp.png")
                                im = matplotlib.image.imread("temp.png")#[-1:0:-1,:,:]
                                buffer.close()
                                fig = Figure(dpi=80, facecolor='none', edgecolor='none')
                                fig.set_alpha(0)
                                fig.set_figheight(height/80.0)
                                fig.set_figwidth(width/80.0) 
                                m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                                        urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                                        #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                                        resolution=None,
                                        lat_ts = 0.0,
                                        suppress_ticks=True)
                                m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])
                                if domain.geom_type == "Polygon":
                                    x, y = domain.exterior.xy
                                    x = numpy.asarray(x)
                                    if continuous is True:
                                        if lonmin < 0:
                                            x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                            x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        else:
                                            #print x.min(), x.max()
                                            #print x[numpy.where(x < lonmax-359)]
                                            x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                    x, y = m(x, y)
                                    #print numpy.asarray((x,y)).T
                                    #print patches.Polygon(numpy.asarray((x,y)).T)
                                    p = patches.Polygon(numpy.asarray((x,y)).T)
                                    m.ax.add_patch(p)
                                    #m.imshow(im, clip_path=p)
                                    fig.figimage(im, clip_path=p)
                                    p.set_color('none')
                                    try:
                                        for hole in domain.interiors:
                                            #print hole
                                            x, y = hole.xy
                                            x = numpy.asarray(x)
                                            if continuous is True:
                                                if lonmin < 0:
                                                    x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                    x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                else:
                                                    x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                            x, y = m(x, y)
                                            p = patches.Polygon(numpy.asarray((x,y)).T)
                                            #print p
                                            m.ax.add_patch(p)
                                            #m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p)
                                            p.set_color('w')
                                    except:
                                        print "passing"
                                    

                                elif domain.geom_type == "MultiPolygon":
                                    for part in domain.geoms:
                                        x, y = part.exterior.xy
                                        x = numpy.asarray(x)
                                        if continuous is True:
                                            if lonmin < 0:
                                                x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                            else:
                                                x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        x, y = m(x, y)
                                        #print numpy.asarray((x,y)).T
                                        #print patches.Polygon(numpy.asarray((x,y)).T)
                                        p = patches.Polygon(numpy.asarray((x,y)).T)
                                        m.ax.add_patch(p)
                                        #m.imshow(im, clip_path=p)
                                        fig.figimage(im, clip_path=p)
                                        p.set_color('none')
                                        try:
                                            for hole in domain.interiors:
                                                #print hole
                                                x, y = hole.xy
                                                x = numpy.asarray(x)
                                                if continuous is True:
                                                    if lonmin < 0:
                                                        x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                        x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                    else:
                                                        x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                x, y = m(x, y)
                                                p = patches.Polygon(numpy.asarray((x,y)).T)
                                                #print p 
                                                m.ax.add_patch(p)
                                                #m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p)
                                                p.set_color('w')
                                        except:
                                            print "passing"
                                            
                                #qq = m.contourf(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, levels=levs, antialiased=True)
                            else:
                                lonn, latn = m(lonn, latn)
                                tri = Tri.Triangulation(lonn, latn, triangles=nv)
                                m.ax.tricontour(tri, mag, norm=CNorm, levels=levs, antialiased=True, linewidth=2)           

                        elif "filledcontours" in actions:
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  
                            
                            if len(variables) > 1:
                                mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2) 
                                mag = numpy.sqrt(mag)
                            else:
                                if magnitude == "True":
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
                            
                            
                            if topology_type.lower() == 'cell':
                                #print dir(m)
                                import shapely.geometry
                                import matplotlib.patches as patches
                                
                                lon, lat = m(lon, lat)
                                trid = Tri.Triangulation(lon, lat)
                                m.ax.tricontourf(trid, mag, norm=CNorm, levels=levs, antialiased=False, linewidth=0)
                                
                                f = open(os.path.join(config.topologypath, dataset + '.domain'))
                                domain = pickle.load(f)
                                f.close()
                                if continuous is True:
                                    if lonmin < 0:
                                        #x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                        #x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 0, latmax),
                                                                             shapely.geometry.box(0, latmin, lonmax, latmax)))
                                    else:
                                        box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 180, latmax),
                                                                             shapely.geometry.box(-180, latmin, lonmax-360, latmax)))
                                else:
                                    box = shapely.geometry.box(lonmin, latmin, lonmax, latmax)
                                
                                domain = domain.intersection(box)
                                
                                buffer = StringIO()
                            
                                lonmax1, latmax1 = m(lonmax, latmax)
                                lonmin1, latmin1 = m(lonmin, latmin)
                                m.ax.set_xlim(lonmin1, lonmax1)
                                m.ax.set_ylim(latmin1, latmax1)
                                m.ax.set_frame_on(False)
                                m.ax.set_clip_on(False)
                                m.ax.set_position([0,0,1,1])
                    
                                canvas = FigureCanvasAgg(fig)
                                canvas.print_png("temp.png")
                                im = matplotlib.image.imread("temp.png")#[-1:0:-1,:,:]
                                buffer.close()
                                fig = Figure(dpi=80, facecolor='none', edgecolor='none')
                                fig.set_alpha(0)
                                fig.set_figheight(height/80.0)
                                fig.set_figwidth(width/80.0) 
                                m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                                        urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                                        #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2,                              
                                        resolution=None,
                                        lat_ts = 0.0,
                                        suppress_ticks=True)
                                m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])
                                if domain.geom_type == "Polygon":
                                    x, y = domain.exterior.xy
                                    x = numpy.asarray(x)
                                    if continuous is True:
                                        if lonmin < 0:
                                            x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                            x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        else:
                                            #print x.min(), x.max()
                                            #print x[numpy.where(x < lonmax-359)]
                                            x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                    x, y = m(x, y)
                                    #print numpy.asarray((x,y)).T
                                    #print patches.Polygon(numpy.asarray((x,y)).T)
                                    p = patches.Polygon(numpy.asarray((x,y)).T)
                                    m.ax.add_patch(p)
                                    #m.imshow(im, clip_path=p)
                                    fig.figimage(im, clip_path=p)
                                    p.set_color('none')
                                    try:
                                        for hole in domain.interiors:
                                            #print hole
                                            x, y = hole.xy
                                            x = numpy.asarray(x)
                                            if continuous is True:
                                                if lonmin < 0:
                                                    x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                    x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                else:
                                                    x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                            x, y = m(x, y)
                                            p = patches.Polygon(numpy.asarray((x,y)).T)
                                            #print p
                                            m.ax.add_patch(p)
                                            #m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p)
                                            p.set_color('w')
                                    except:
                                        print "passing"
                                    

                                elif domain.geom_type == "MultiPolygon":
                                    for part in domain.geoms:
                                        x, y = part.exterior.xy
                                        x = numpy.asarray(x)
                                        if continuous is True:
                                            if lonmin < 0:
                                                x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                            else:
                                                x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        x, y = m(x, y)
                                        #print numpy.asarray((x,y)).T
                                        #print patches.Polygon(numpy.asarray((x,y)).T)
                                        p = patches.Polygon(numpy.asarray((x,y)).T)
                                        m.ax.add_patch(p)
                                        #m.imshow(im, clip_path=p)
                                        fig.figimage(im, clip_path=p)
                                        p.set_color('none')
                                        try:
                                            for hole in domain.interiors:
                                                #print hole
                                                x, y = hole.xy
                                                x = numpy.asarray(x)
                                                if continuous is True:
                                                    if lonmin < 0:
                                                        x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                        x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                    else:
                                                        x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                x, y = m(x, y)
                                                p = patches.Polygon(numpy.asarray((x,y)).T)
                                                #print p 
                                                m.ax.add_patch(p)
                                                #m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p)
                                                p.set_color('w')
                                        except:
                                            print "passing"
                                
                                #qq = m.contourf(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, levels=levs, antialiased=True)
                            else:
                                lonn, latn = m(lonn, latn)
                                tri = Tri.Triangulation(lonn, latn, triangles=nv)
                                m.ax.tricontourf(tri, mag, norm=CNorm, levels=levs, antialiased=False, linewidth=0)   
                                
                            
                            
                        elif "pcolor" in actions:
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)  
                            if topology_type.lower() == "cell":
                                lon, lat = m(lon, lat)
                                lonn, latn = m(lonn, latn)
                            else:
                                lon, lat = m(lonn, latn)
                                lonn, latn = lon, lat
                                
                            if len(variables) > 1:
                                mag = numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2)
                                mag = numpy.sqrt(mag)
                            else:
                                if magnitude == "True":
                                    mag = numpy.abs(var1)
                                else:
                                    mag = var1
                            
                            #ax = fig.add_subplot(111)
                            if (climits[0] == "None") or (climits[1] == "None"):
                                CNorm = matplotlib.colors.Normalize()
                            else:
                                CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                                    vmax=climits[1],
                                                                    clip=True,
                                                                   )
                                                                   
                            #tri = Tri.Triangulation(lonn,latn,triangles=nv)
                           
                            #m.pcolor(numpy.asarray(lon), numpy.asarray(lat), numpy.asarray(mag), tri=True, norm=CNorm, rasterized=True)
                            #xi = numpy.arange(lon.min(), lon.max(), 1000)
                            #yi = numpy.arange(lat.min(), lat.max(), 1000)
                            #print "lon " + str(lonmax-lonmin), lonmax, lonmin
                            if lonmax-lonmin < 3:
                                num = 300
                            elif lonmax-lonmin < 5:
                                num = 500
                            elif lonmax-lonmin < 9:
                                num = 900
                            else:
                                num = 2500
                            #num = int( (lonmax - lonmin) *  100 )
                            xi = numpy.arange(m.xmin, m.xmax, num)
                            yi = numpy.arange(m.ymin, m.ymax, num)

                            from matplotlib.mlab import griddata

                            if topology_type.lower() == "node":
                                n = numpy.unique(nv)
                                print "lon " , lon[n].min(), lon[n].max()
                                print "xi", xi.min(), xi.max()
                                zi = griddata(lon[n], lat[n], mag[n], xi, yi, interp='nn')
                            else:
                                zi = griddata(lon, lat, mag, xi, yi, interp='nn')

                            import matplotlib.patches as patches

                            #a = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]
                            #b = [(1, 1), (1, 2), (2, 2), (2, 1), (1, 1)]
                            #multi1 = MultiPolygon([[a, []], [b, []]])
                            print timeobj.time() - totaltimer
                            
                            f = open(os.path.join(config.topologypath, dataset + '.domain'))
                            domain = pickle.load(f)
                            f.close()
                            import shapely.geometry
                            if continuous is True:
                                if lonmin < 0:
                                    #x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                    #x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                    box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 0, latmax),
                                                                         shapely.geometry.box(0, latmin, lonmax, latmax)))
                                else:
                                    box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 180, latmax),
                                                                         shapely.geometry.box(-180, latmin, lonmax-360, latmax)))
                            else:
                                box = shapely.geometry.box(lonmin, latmin, lonmax, latmax)
                            domain = domain.intersection(box)
                            print lonmin, latmin, lonmax, latmax
                            print timeobj.time() - totaltimer
                            
                            if domain.geom_type == "Polygon":
                                x, y = domain.exterior.xy
                                x = numpy.asarray(x)
                                if continuous is True:
                                    if lonmin < 0:
                                        x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                        x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                    else:
                                        #print x.min(), x.max()
                                        #print x[numpy.where(x < lonmax-359)]
                                        x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                x, y = m(x, y)
                                #print numpy.asarray((x,y)).T
                                #print patches.Polygon(numpy.asarray((x,y)).T)
                                p = patches.Polygon(numpy.asarray((x,y)).T)
                                m.ax.add_patch(p)
                                m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p, interpolation="nearest")
                                p.set_color('none')
                                try:
                                    for hole in domain.interiors:
                                        #print hole
                                        x, y = hole.xy
                                        x = numpy.asarray(x)
                                        if continuous is True:
                                            if lonmin < 0:
                                                x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                            else:
                                                x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        x, y = m(x, y)
                                        p = patches.Polygon(numpy.asarray((x,y)).T)
                                        #print p
                                        m.ax.add_patch(p)
                                        #m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p)
                                        p.set_color('w')
                                except:
                                    print "passing"
                                

                            elif domain.geom_type == "MultiPolygon":
                                for part in domain.geoms:
                                    x, y = part.exterior.xy
                                    x = numpy.asarray(x)
                                    if continuous is True:
                                        if lonmin < 0:
                                            x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                            x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                        else:
                                            x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                    x, y = m(x, y)
                                    #print numpy.asarray((x,y)).T
                                    #print patches.Polygon(numpy.asarray((x,y)).T)
                                    p = patches.Polygon(numpy.asarray((x,y)).T)
                                    m.ax.add_patch(p)
                                    m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p, interpolation="nearest")
                                    p.set_color('none')
                                    try:
                                        for hole in domain.interiors:
                                            #print hole
                                            x, y = hole.xy
                                            x = numpy.asarray(x)
                                            if continuous is True:
                                                if lonmin < 0:
                                                    x[numpy.where(x > 0)] = x[numpy.where(x > 0)] - 360
                                                    x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                                else:
                                                    x[numpy.where(x < lonmax-359)] = x[numpy.where(x < lonmax-359)] + 360
                                            x, y = m(x, y)
                                            p = patches.Polygon(numpy.asarray((x,y)).T)
                                            #print p 
                                            m.ax.add_patch(p)
                                            #m.imshow(zi, norm=CNorm, cmap=colormap, clip_path=p)
                                            p.set_color('w')
                                    except:
                                        print "passing"
                            
                        elif  "facets" in actions:
                            #projection = request.GET["projection"]
                            #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                            #            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                            #            lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                            #            )
                            fig.set_figheight(height/80.0)
                            fig.set_figwidth(width/80.0)
                            
                            #print "points ll", numpy.min(lonn), numpy.min(latn), "ur", numpy.max(lonn), numpy.max(latn)
                            lonn, latn = m(lonn, latn)
                            tri = Tri.Triangulation(lonn,latn,triangles=nv)
                            if len(variables) > 1:
                                mag = numpy.sqrt(numpy.power(var1.__abs__(), 2)+numpy.power(var2.__abs__(), 2))
                            else:
                                if magnitude == "True":
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
                                                                    
                            if topology_type.lower() == 'cell':
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
                            import pywms.wms.regrid as regrid
                            
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
            #job_server.destroy() # important so that we dont keep spwaning workers on every call, real messy...
                        
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
            
    topology.close()
    gc.collect()
    print timeobj.time() - totaltimer
    return response

def fvWps (request):
    pass
    return HttpResponse
