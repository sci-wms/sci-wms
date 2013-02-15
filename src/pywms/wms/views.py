'''
Created on Sep 1, 2011

@author: ACrosby
'''
import sys, os, gc, bisect, math, datetime, numpy, netCDF4, multiprocessing, logging, traceback

# Import from matplotlib and set backend
import matplotlib
matplotlib.use("Agg")
from mpl_toolkits.basemap import Basemap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from rtree import rindex

# Other random "from" imports
from collections import deque
from StringIO import StringIO # will be deprecated in Python3, use io.byteIO instead
import time as timeobj
try:
    import cPickle as pickle
except ImportError:
    import Pickle as pickle
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

# Import from sci-wms
from pywms.wms.models import Dataset, Server
from django.contrib.sites.models import Site
import pywms.grid_init_script as grid_cache
from pywms.wms import cgrid, ugrid
from django.http import HttpResponse, HttpResponseRedirect
import pywms.server_local_config as config

output_path = os.path.join(config.fullpath_to_wms, 'src', 'pywms', 'sciwms_wms')
# Set up Logger
logger = multiprocessing.get_logger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler('%s.log' % output_path)
formatter = logging.Formatter(fmt='[%(asctime)s] - <<%(levelname)s>> - |%(message)s|')
handler.setFormatter(formatter)
logger.addHandler(handler)

def testdb(request):
    #print dir(Dataset.objects.get(name='necofs'))
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
    grid_cache.check_topology_age()
    from django.template import Context, Template
    f = open(os.path.join(config.staticspath, "wms_openlayers_test.html"))
    text = f.read()
    f.close()
    sites = Site.objects.values()
    dict1 = Context({ 'localsite':sites[0]['domain'],
                      'datasets':Dataset.objects.values()})
    return HttpResponse(Template(text).render(dict1))
    
def leaflet (request):
    from django.template import Context, Template
    f = open(os.path.join(config.staticspath, "leaflet_example.html"))
    text = f.read()
    f.close()
    sites = Site.objects.values()
    dict1 = Context({ 'localsite':sites[0]['domain'],
                      'datasets':Dataset.objects.values()})
    return HttpResponse(Template(text).render(dict1))

def update (request):
    logger.info("Adding new datasets and checking for updates on old ones...")
    grid_cache.check_topology_age()
    logger.info("...Finished updating")
    return HttpResponse("Updating Started, for large datasets or many datasets this may take a while")

def add(request):
    return HttpResponse()

def remove(request):
    return HttpResponse()

def documentation (request):
##    #jobsarray = grid_cache.check_topology_age()
##    import django.shortcuts as dshorts
##    import os
##    #import pywms.server_local_config as config
##    f = open(os.path.join(config.fullpath_to_wms, "README.md"))
##    text = f.read()
##    dict1 = { "textfile":text}
##    return dshorts.render_to_response('docs.html', dict1)
    return HttpResponseRedirect('http://acrosby.github.com/sci-wms')

def crossdomain (request):
    f = open(config.staticspath + "crossdomain.xml")
    test = f.read()
    response = HttpResponse(content_type="text/xml")
    response.write(test)
    return response

def wms (request, dataset):
    try:
        try:
            reqtype = request.GET['REQUEST']
        except:
            reqtype = request.GET['request']
        if reqtype.lower() == 'getmap':
            import pywms.wms.wms_handler as wms
            handler = wms.wms_handler(request)
            action_request = handler.make_action_request(request)
            if action_request is not None:
                response = getMap(action_request, dataset, logger)
            else:
                response = HttpResponse()
        elif reqtype.lower() == 'getfeatureinfo':
            response =  getFeatureInfo(request, dataset, logger)
        elif reqtype.lower() == 'getlegendgraphic':
            response =  getLegendGraphic(request, dataset, logger)
        elif reqtype.lower() == 'getcapabilities':
            response = getCapabilities(request, dataset, logger)
        logger.info(str(request.GET))
        return response
    except Exception as detail:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error("Status 500 Error: " +\
                     repr(traceback.format_exception(exc_type, exc_value,
                                  exc_traceback)) + '\n' + str(request))
        return HttpResponse("problem", status=500)

def getCapabilities(req, dataset, logger): # TODO move get capabilities to template system like sciwps
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
    ET.SubElement(gfi, "Format").text = "text/csv"
    ET.SubElement(gfi, "Format").text = "text/javascript"
    #ET.SubElement(gfi, "Format").text = "text/csv"
    #ET.SubElement(gfi, "Format").text = "application/netcdf"
    #ET.SubElement(gfi, "Format").text = "application/matlab-mat"
    #ET.SubElement(gfi, "Format").text = "application/x-zip-esrishp"
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
            if topology.grid != 'False':
                location = "grid"
            else:
                location = "node"
        if location == "face":
            location = "cell"
        try:
            #nc.variables[variable].location
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
            llbbox.attrib["minx"] = str(topology.variables["lon"][:].min())
            llbbox.attrib["miny"] = str(topology.variables["lat"][:].min())
            llbbox.attrib["maxx"] = str(topology.variables["lon"][:].max())
            llbbox.attrib["maxy"] = str(topology.variables["lat"][:].max())
            llbbox = ET.SubElement(layer1, "BoundingBox")
            llbbox.attrib["SRS"] = "EPSG:4326"
            llbbox.attrib["minx"] = str(topology.variables["lon"][:].min())
            llbbox.attrib["miny"] = str(topology.variables["lat"][:].min())
            llbbox.attrib["maxx"] = str(topology.variables["lon"][:].max())
            llbbox.attrib["maxy"] = str(topology.variables["lat"][:].max())
            time_dimension = ET.SubElement(layer1, "Dimension")
            time_dimension.attrib["name"] = "time"
            time_dimension.attrib["units"] = "ISO8601"
            elev_dimension = ET.SubElement(layer1, "Dimension")
            elev_dimension.attrib["name"] = "elevation"
            elev_dimension.attrib["units"] = "EPSG:5030"
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
            
            ## Listing all available elevation layers is a tough thing to do for the range of types of datasets...
            if topology.grid.lower() == 'false':
                if nc.variables[variable].ndim > 2:
                    try:
                        ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables["siglay"].shape[0])).replace("[","").replace("]","").replace(" ", "")
                        elev_extent.text = str(range(nc.variables["siglay"].shape[0])).replace("[","").replace("]","").replace(" ", "")
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
                    elev_extent.text = "0"
            elif topology.grid.lower() =='cgrid':
                if nc.variables[variable].ndim > 3:
                    try:
                        ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables[variable].shape[1])).replace("[","").replace("]","").replace(" ", "")
                        elev_extent.text = str(range(nc.variables[variable].shape[1])).replace("[","").replace("]","").replace(" ", "")
                    except:
                        ET.SubElement(layer1, "DepthLayers").text = ""
                    try:
                        #if nc.variables["depth"].positive.lower() == "up":
                        #    ET.SubElement(layer1, "DepthDirection").text = "Down"
                        #elif nc.variables["depth"].positive.lower() == "down":
                        #    ET.SubElement(layer1, "DepthDirection").text = "Up"
                        #else:
                        #    ET.SubElement(layer1, "DepthDirection").text = ""
                        ET.SubElement(layer1, "DepthDirection").text = ""
                    except:
                        ET.SubElement(layer1, "DepthDirection").text = ""
                else:
                    ET.SubElement(layer1, "DepthLayers").text = "0"
                    ET.SubElement(layer1, "DepthDirection").text = "Down"
                    elev_extent.text = "0"
            else:
                ET.SubElement(layer1, "DepthLayers").text = "0"
                ET.SubElement(layer1, "DepthDirection").text = "Down"
                elev_extent.text = "0"
            ##
            
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
            if variable == "u" or variable == "u-vel" or variable == "ua" or variable=="U" or variable=="uc" or variable=="air_u" or variable=="water_u":
                if variable == "u":
                    layername = "u,v"
                elif variable == "u-vel":
                    layername = "u-vel,v-vel"
                elif variable == "ua":
                    layername = "ua,va"
                elif variable == "uc":
                    layername = "uc,vc"
                elif variable == "U":
                    layername = "U,V"
                elif variable == "air_u":
                    layername = "air_u,air_v"
                elif variable == "water_u":
                    layername = "water_u,water_v"
                try:
                    location = nc.variables[variable].location
                except:
                    if topology.grid != 'False':
                        location = "grid"
                    else:
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
                llbbox.attrib["minx"] = str(topology.variables["lon"][:].min())
                llbbox.attrib["miny"] = str(topology.variables["lat"][:].min())
                llbbox.attrib["maxx"] = str(topology.variables["lon"][:].max())
                llbbox.attrib["maxy"] = str(topology.variables["lat"][:].max())
                llbbox = ET.SubElement(layer1, "BoundingBox")
                llbbox.attrib["SRS"] = "EPSG:4326"
                llbbox.attrib["minx"] = str(topology.variables["lon"][:].min())
                llbbox.attrib["miny"] = str(topology.variables["lat"][:].min())
                llbbox.attrib["maxx"] = str(topology.variables["lon"][:].max())
                llbbox.attrib["maxy"] = str(topology.variables["lat"][:].max())
                time_dimension = ET.SubElement(layer1, "Dimension")
                time_dimension.attrib["name"] = "time"
                time_dimension.attrib["units"] = "ISO8601"
                elev_dimension = ET.SubElement(layer1, "Dimension")
                elev_dimension.attrib["name"] = "elevation"
                elev_dimension.attrib["units"] = "EPSG:5030"
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
                    elev_extent.text = "0"
                    ET.SubElement(layer1, "DepthDirection").text = "Down"
                for style in ["vectors", "barbs"]:
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
        except:
            pass
    nc.close()
    tree = ET.ElementTree(root)
    try:
        if req.GET["FORMAT"].lower() == "text/javascript":
            import json
            output_dict = {}
            output_dict["capabilities"] = r'<?xml version="1.0" encoding="utf-8"?>' + ET.tostring(root)
            callback = "parseResponse"
            try:
                callback = request.GET["CALLBACK"]
            except:
                pass
            try:
                callback = request.GET["callback"]
            except:
                pass
            response = HttpResponse(content_type="text/javascript")
            output_str = callback + "(" + json.dumps(output_dict, indent=4, separators=(',',': '), allow_nan=True) + ")"
            response.write(output_str)
        else:
            # Return the response
            response = HttpResponse(content_type="text/xml")
            response.write(r'<?xml version="1.0" encoding="utf-8"?>')
            tree.write(response)
    except:
        # Return the response
        response = HttpResponse(content_type="text/xml")
        response.write(r'<?xml version="1.0" encoding="utf-8"?>')
        tree.write(response)
    return response

def getLegendGraphic(request, dataset, logger):
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
    colormap = styles[2].replace('-', '_')

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
    from matplotlib.pylab import get_cmap
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
                                              cmap=get_cmap(colormap),
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
            logger.info( str((levels, levs)) )
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
    nc.close()
    return response


def getFeatureInfo(request, dataset, logger):
    """
     /wms/GOM3/?ELEVATION=1&LAYERS=temp&FORMAT=image/png&TRANSPARENT=TRUE&STYLES=facets_average_jet_0_32_node_False&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&SRS=EPSG:3857&BBOX=-7949675.196111,5078194.822174,-7934884.63114,5088628.476533&X=387&Y=196&INFO_FORMAT=text/csv&WIDTH=774&HEIGHT=546&QUERY_LAYERS=salinity&TIME=2012-08-14T00:00:00/2012-08-16T00:00:00
    """
    from datetime import date
    from mpl_toolkits.basemap import pyproj
    #totaltimer = timeobj.time()
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

    vhaversine = numpy.vectorize(haversine)

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
    INFO_FORMAT = "text/csv" # request.GET['INFO_FORMAT']
    projection = 'merc'#request.GET['SRS']
    #TIME = request.GET['TIME']
    try:
        elevation = int(request.GET['ELEVATION'])
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

    topology = netCDF4.Dataset(os.path.join(config.topologypath, dataset + '.nc'))
    gridtype = topology.grid
    if gridtype == 'False':
        if 'node' in styles:
            tree = rindex.Index(dataset+'_nodes')
            lats = topology.variables['lat'][:]
            lons = topology.variables['lon'][:]
        else:
            tree = rindex.Index(dataset+'_cells')
            lats = topology.variables['latc'][:]
            lons = topology.variables['lonc'][:]
        #print 'time before haversine ' + str(timeobj.time() - totaltimer)
        nindex = list(tree.nearest((lon, lat, lon, lat), 1, objects=True))
        selected_longitude, selected_latitude = tuple(nindex[0].bbox[:2])
        index = nindex[0].id
        tree.close()
    else:
        """
        lats = topology.variables['lat'][:]
        lons = topology.variables['lon'][:]
        #print 'time before haversine ' + str(timeobj.time() - totaltimer)
        lengths = vhaversine(lat, lon, lats, lons)
        # TODO: Replace this methodology with the rtree one
        min = numpy.asarray(lengths)
        min = numpy.min(min)
        index = numpy.where(lengths==min)
        selected_latitude = lats[index][0]
        selected_longitude = lons[index][0]
        """
        tree = rindex.Index(dataset+'_nodes')
        lats = topology.variables['lat'][:]
        lons = topology.variables['lon'][:]
        #print 'time before haversine ' + str(timeobj.time() - totaltimer)
        nindex = list(tree.nearest((lon, lat, lon, lat), 1, objects=True))
        selected_longitude, selected_latitude = lons[nindex[0][0],nindex[0][1]], lats[nindex[0][0],nindex[0][1]]
        index = nindex[0]
        tree.close()
    #print 'final time to complete haversine ' + str(timeobj.time() - totaltimer)
    try:
        TIME = request.GET["TIME"]
        if TIME == "":
            now = date.today().isoformat()
            TIME = now + "T00:00:00"#
    except:
        now = date.today().isoformat()
        TIME = now + "T00:00:00"#
        #print "here"
    TIMES = TIME.split("/")
    #print TIMES
    for i in range(len(TIMES)):
##            print TIMES[i]
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
        datestart = netCDF4.date2num(datestart, units=time_units)
        dateend = netCDF4.date2num(dateend, units=time_units)
        time1 = bisect.bisect_right(times, datestart)
        time2 = bisect.bisect_right(times, dateend)
##            print time2
        if time1 == -1:
            time1 = 0
        if time2 == -1:
            time2 = len(times)
##            print time2
        time = range(time1, time2)
        if len(time) < 1:
            time = [len(times) - 1]
    else:
        datestart = datetime.datetime.strptime(TIMES[0], "%Y-%m-%dT%H:%M:%S" )
        times = topology.variables['time'][:]
        time_units = topology.variables['time'].units
        datestart = netCDF4.date2num(datestart, units=time_units)
        time1 = bisect.bisect_right(times, datestart)
        if time1 == -1:
            time = [0]
        else:
            time = [time1]

    pvar = deque()
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

    url = Dataset.objects.get(name=dataset).uri
    datasetnc = netCDF4.Dataset(url)

    varis = deque()
    varis.append(getvar(topology, time, elevation, "time", index))
    if gridtype == 'False':
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
    elif request.GET["INFO_FORMAT"].lower() == "application/json":
        import json
        response = HttpResponse("Response MIME Type application/json not supported at this time")
    elif request.GET["INFO_FORMAT"].lower() == "text/javascript":
        """
        http://docs.geoserver.org/latest/en/user/services/wms/reference.html#getfeatureinfo
        """
        import json
        callback = "parseResponse"
        try:
            callback = request.GET["CALLBACK"]
        except:
            pass
        try:
            callback = request.GET["callback"]
        except:
            pass
        response = HttpResponse()
        output_dict = {}
        output_dict2 = {}
        output_dict["type"] = "Feature"
        output_dict["geometry"] = {"type":"Point", "coordinates":[selected_longitude,selected_latitude]}
        varis[0] = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in varis[0]]
        output_dict2["time"] = {"units": "iso", "values": varis[0]}
        output_dict2["latitude"] = {"units":"degrees_north", "values":float(selected_latitude)}
        output_dict2["longitude"] = {"units":"degrees_east", "values":float(selected_longitude)}
        for i, var in enumerate(QUERY_LAYERS): # TODO: use map to convert to floats
            varis[i+1] = list(varis[i+1])
            for q, v in enumerate(varis[i+1]):
                if numpy.isnan(v):
                    varis[i+1][q] = float("nan")
                else:
                    varis[i+1][q] = float(varis[i+1][q])
            output_dict2[var] = {"units": datasetnc.variables[var].units, "values": varis[i+1]}
        output_dict["properties"] = output_dict2
        output_str = callback + "(" + json.dumps(output_dict, indent=4, separators=(',',': '), allow_nan=True) + ")"
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
                if type(varis[k]) == numpy.ndarray:
                    try:
                        thisline.append(varis[k][i])
                    except:
                        thisline.append(varis[k])
                else: # If the variable is not changing with type, like bathy
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

def getMap (request, dataset, logger):
    '''
    the meat and bones of getMap
    '''
    from mpl_toolkits.basemap import pyproj
    from matplotlib.figure import Figure

    totaltimer = timeobj.time()
    loglist = []

    # direct the service to the dataset
    url = Dataset.objects.get(name=dataset).uri

    # Get the size of image requested and the geographic extent in webmerc
    width = float(request.GET["width"])
    height = float(request.GET["height"])
    latmax = float(request.GET["latmax"])
    latmin = float(request.GET["latmin"])
    lonmax = float(request.GET["lonmax"])
    lonmin = float(request.GET["lonmin"])

    # Get time extents, elevation index(layer), and styles(actions)
    datestart = request.GET["datestart"]
    dateend = request.GET["dateend"]
    layer = request.GET["layer"]
    layer = layer.split(",")
    for i,l in enumerate(layer):
    #    layer[i] = int(l)-1
        layer = int(l)
    layer = numpy.asarray(layer)
    actions = request.GET["actions"]
    actions = set(actions.split(","))

    # Get the colormap requested, the color limits/scaling
    colormap = request.GET["colormap"]#.lower()
    if request.GET["climits"][0] != "None":
        climits = [float(lim) for lim in request.GET["climits"]]
    else:
        climits = ["None", "None"]

    # Get the absolute magnitude bool, the topological location of variable of
    # interest, and the variables of interest (comma sep, no spaces, limit 2)
    magnitude = request.GET["magnitude"]
    topology_type = request.GET["topologytype"]
    variables = request.GET["variables"].split(",")
    continuous = False

    # Get the box coordinates from webmercator to proper lat/lon for grid subsetting
    mi = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs ")
    lonmin, latmin = mi(lonmin, latmin, inverse=True)
    lonmax, latmax = mi(lonmax, latmax, inverse=True)

    if "kml" in actions: # TODO: REMOVE THIS!
        pass
    else:
        # Open topology cache file, and the actualy data endpoint
        topology = netCDF4.Dataset(os.path.join(config.topologypath, dataset + '.nc'))
        datasetnc = netCDF4.Dataset(url)
        gridtype = topology.grid # Grid type found in topology file

        if gridtype != 'False':
            toplatc, toplonc = 'lat', 'lon'
            #toplatn, toplonn = 'lat', 'lon'
        else:
            toplatc, toplonc = 'latc', 'lonc'
            #toplatn, toplonn = 'lat', 'lon'

        # If the request is not a box, then do nothing.
        if latmax != latmin:
            # Pull cell coords out of cache.
            # Deal with the longitudes of a global file so that it adheres to
            # the -180/180 convention.
            if lonmin > lonmax:
                lonmax = lonmax + 360
                continuous = True
                lon = topology.variables[toplonc][:]
                wher = numpy.where(lon<lonmin)
                lon[wher] = lon[wher] + 360
            else:
                lon = topology.variables[toplonc][:]
            lat = topology.variables[toplatc][:]
            if gridtype != 'False':
                if gridtype == 'cgrid':
                    index, lat, lon = cgrid.subset(latmin, lonmin, latmax, lonmax, lat, lon)
            else:
                index, lat, lon = ugrid.subset(latmin, lonmin, latmax, lonmax, lat, lon)
            if gridtype == 'False': # TODO: Get rid of thiss whole chunk!
                try:
                    loglist.append("index " + len(index))
                except:
                    loglist.append("index " + str(index))
            else:
                try:
                    loglist.append("index " + str(index.shape))
                except:
                    loglist.append("index " + str(index))

        if index is not None:
            if ("facets" in actions) or \
            ("regrid" in actions) or \
            ("shape" in actions) or \
            ("contours" in actions) or \
            ("interpolate" in actions) or \
            ("filledcontours" in actions) or \
            ("pcolor" in actions) or \
            (topology_type.lower()=='node'):
                if gridtype == 'False': # If ugrid
                    # If the nodes are important, get the node coords, and
                    # topology array
                    import matplotlib.tri as Tri
                    nv = ugrid.get_topologyarray(topology, index)
                    latn, lonn = ugrid.get_nodes(topology)
                    if topology_type.lower() == "node":
                        index = range(len(latn))
                    # Deal with global out of range datasets in the node longitudes
                    if continuous is True:
                        if lonmin < 0:
                            lonn[numpy.where(lonn > 0)] = lonn[numpy.where(lonn > 0)] - 360
                            lonn[numpy.where(lonn < lonmax-359)] = lonn[numpy.where(lonn < lonmax-359)] + 360
                        else:
                            lonn[numpy.where(lonn < lonmax-359)] = lonn[numpy.where(lonn < lonmax-359)] + 360
                else:
                    pass # If regular grid, do nothing
            else:
                nv = None
                lonn, latn = None, None

            times = topology.variables['time'][:]
            datestart = datetime.datetime.strptime( datestart, "%Y-%m-%dT%H:%M:%S" ) # datestr --> datetime obj
            datestart = netCDF4.date2num(datestart, units=topology.variables['time'].units) # datetime obj --> netcdf datenum
            time = bisect.bisect_right(times, datestart) - 1
            if config.localdataset:
                time = [1]
            elif time == -1:
                time = [0]
            else:
                time = [time]
            if dateend != datestart:
                dateend = datetime.datetime.strptime( dateend, "%Y-%m-%dT%H:%M:%S" ) # datestr --> datetime obj
                dateend = netCDF4.date2num(dateend, units=topology.variables['time'].units) # datetime obj --> netcdf datenum
                time.append(bisect.bisect_right(times, dateend) - 1)
                if config.localdataset:
                    time[1] = 1
                elif time[1] == -1:
                    time[1] = 0
                else:
                    time[1] = time[1]
                time = range(time[0], time[1]+1)
            t = time # TODO: ugh this is bad
            loglist.append('time index requested ' + str(time))

            # Get the data and appropriate resulting shape from the data source
            if gridtype == 'False':
                var1, var2 = ugrid.getvar(datasetnc, t, layer, variables, index)
            if gridtype == 'cgrid':
                index = numpy.asarray(index)
                var1, var2 = cgrid.getvar(datasetnc, t, layer, variables, index)
            
            if latmin != latmax: # TODO: REMOVE THIS CHECK ALREADY DONE ABOVE
                if gridtype == 'False': # TODO: Should take a look at this
                    # This is averaging in time over all timesteps downloaded
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
                    # This finding max in time over all timesteps downloaded
                    if "maximum" in actions:
                        if len(var1.shape) > 2:
                            var1 = numpy.abs(var1).max(axis=0)
                            var1 = numpy.abs(var1).max(axis=0)
                            try:
                                var2 = numpy.abs(var2).max(axis=0)
                                var2 = numpy.abs(var2).max(axis=0)
                            except:
                                pass
                        elif len(var1.shape) > 1:
                            var1 = numpy.abs(var1).max(axis=0)
                            try:
                                var2 = numpy.abs(var2).max(axis=0)
                            except:
                                pass

                # Setup the basemap/matplotlib figure
                fig = Figure(dpi=80, facecolor='none', edgecolor='none')
                fig.set_alpha(0)
                projection = request.GET["projection"]
                m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin,
                        urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                        resolution=None,
                        lat_ts = 0.0,
                        suppress_ticks=True)
                m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])
                try: # Fail gracefully if not standard_name, should do this a little better than a try
                    if 'direction' in datasetnc.variables[variables[1]].standard_name:
                        #assign new var1,var2 as u,v components
                        var2 = 450 - var2
                        var2[var2>360] = var2[var2>360] - 360
                        var2 = numpy.sin(numpy.radians(var2)) * var1 # var 2 needs to come first so that
                        var1 = numpy.cos(numpy.radians(var2)) * var1 # you arn't multiplying by the wrong var1 val
                except:
                    pass
                
                # Close remote dataset and local cache
                topology.close()
                datasetnc.close()
            
                if (climits[0] == "None") or (climits[1] == "None"):
                    CNorm = matplotlib.colors.Normalize()
                else:
                    CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                    vmax=climits[1],
                                                    clip=True,
                                                    )
                # Plot to the projected figure axes!
                if gridtype == 'cgrid':
                    lon, lat = m(lon, lat)
                    cgrid.plot(lon, lat, var1, var2, actions, m.ax, fig,
                                aspect=m.aspect,
                                height=height,
                                width=width,
                                norm=CNorm,
                                cmin = climits[0],
                                cmax = climits[1],
                                magnitude = magnitude,
                                cmap = colormap,
                                basemap = m,
                                lonmin = lonmin,
                                latmin = latmin,
                                lonmax = lonmax,
                                latmax = latmax,
                                )
                elif gridtype == 'False':
                    fig, m = ugrid.plot(lon, lat, lonn, latn, nv, var1, var2, actions, m, m.ax, fig,
                                        aspect=m.aspect,
                                        height=height,
                                        width=width,
                                        norm=CNorm,
                                        cmin = climits[0],
                                        cmax = climits[1],
                                        magnitude = magnitude,
                                        cmap = colormap,
                                        topology_type = topology_type,
                                        lonmin = lonmin,
                                        latmin = latmin,
                                        lonmax = lonmax,
                                        latmax = latmax,
                                        dataset = dataset,
                                        continuous = continuous,
                                        projection = projection,
                                        )
                lonmax, latmax = m(lonmax, latmax)
                lonmin, latmin = m(lonmin, latmin)
                m.ax.set_xlim(lonmin, lonmax)
                m.ax.set_ylim(latmin, latmax)
                m.ax.set_frame_on(False)
                m.ax.set_clip_on(False)
                m.ax.set_position([0,0,1,1])
                canvas = FigureCanvasAgg(fig)
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
        else:
            fig = Figure(dpi=5, facecolor='none', edgecolor='none')
            fig.set_alpha(0)
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
    loglist.append('final time to complete request ' + str(timeobj.time() - totaltimer))
    logger.info(str(loglist))
    return response


