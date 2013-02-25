'''
Created on Oct 17, 2011

@author: ACrosby
'''
from datetime import date

class wms_handler(object):
    '''
    classdocs
    '''
    def make_action_request(self, requestobj):
        try:
            layers = requestobj.GET["LAYERS"]
        except:
            layers = requestobj.GET["layers"]
        try:
            levels = requestobj.GET["ELEVATION"]
            if levels == "":
                levels = "0"
        except:
            levels = "0"
        '''
        Implement more styles and things here
        '''
        try:
            time = requestobj.GET["TIME"]
            if time == "":
                now = date.today().isoformat()
                time = now + "T00:00:00"#
        except:
            now = date.today().isoformat()
            time = now + "T00:00:00"#
        time = time.split("/")
        #print time
        for i in range(len(time)):
            #print time[i]
            time[i] = time[i].replace("Z", "")
            if len(time[i]) == 16:
                time[i] = time[i] + ":00"
            elif len(time[i]) == 13:
                time[i] = time[i] + ":00:00"
            elif len(time[i]) == 10:
                time[i] = time[i] + "T00:00:00"
        if len(time) > 1:
            timestart = time[0]
            timeend = time[1]
        else:
            timestart = time[0]
            timeend = time[0]
        try:
            box = requestobj.GET["BBOX"]
        except:
            box = requestobj.GET["bbox"]
        box = box.split(",")
        latmin = box[1]
        latmax = box[3]
        lonmin = box[0]
        lonmax = box[2]

        try:
            height = requestobj.GET["HEIGHT"]
            width = requestobj.GET["WIDTH"]
            styles = requestobj.GET["STYLES"].split(",")[0].split("_")
        except:
            height = requestobj.GET["height"]
            width = requestobj.GET["width"]
            styles = requestobj.GET["styles"].split(",")[0].split("_")

        colormap = styles[2].replace("-", "_")
        climits = styles[3:5]
        topology_type = styles[5]
        magnitude_bool = styles[6]
        #reqtype = requestobj.GET["REQUEST"]

        class action_request:
            pass

        action_request.GET = {u'latmax':latmax, u'lonmax':lonmax,
                          u'projection':u'merc', u'layer':levels,
                          u'datestart':timestart, u'dateend':timeend,
                          u'lonmin':lonmin, u'latmin':latmin,
                          u'height':height, u'width':width,
                          u'actions':("image," + \
                          "," + styles[0] + "," + styles[1]),
                          u'colormap': colormap,
                          u'climits': climits,
                          u'variables': layers,
                          u'topologytype': topology_type,
                          u'magnitude': magnitude_bool,
                          }
        if float(lonmax)-float(lonmin) < .0001:
            action_request == None
        return action_request



    def __init__(self, requestobj):
        '''
        Constructor
        '''
        self.request = requestobj
'''
def getCapabilities(request, dataset, logger): # TODO move get capabilities to template system like sciwps
    """
    get capabilities document based on this getcaps:


    http://coastmap.com/ecop/wms.aspx?service=WMS&version=1.1.1&request=getcapabilities

    """
    import sys, os, gc, bisect, math, datetime, numpy, netCDF4, multiprocessing, logging, traceback
    # Import from matplotlib and set backend
    import matplotlib
    matplotlib.use("Agg")
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg

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
                    ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables["siglay"].shape[0])).replace("[","").replace("]","")
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
                elev_extent.text = "0"
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
    import sys, os, gc, bisect, math, datetime, numpy, netCDF4, multiprocessing, logging, traceback
    # Import from matplotlib and set backend
    import matplotlib
    matplotlib.use("Agg")
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg

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
    import sys, os, gc, bisect, math, datetime, numpy, netCDF4, multiprocessing, logging, traceback
    # Import from matplotlib and set backend
    import matplotlib
    matplotlib.use("Agg")
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg

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
    box = request.GET["BBOX"]
    box = box.split(",")
    latmin = float(box[1])
    latmax = float(box[3])
    lonmin = float(box[0])
    lonmax = float(box[2])
    height = float(request.GET["HEIGHT"])
    width = float(request.GET["WIDTH"])
    styles = request.GET["STYLES"].split(",")[0].split("_")
    QUERY_LAYERS = request.GET['QUERY_LAYERS'].split(",")
    INFO_FORMAT = "text/plain" # request.GET['INFO_FORMAT']
    projection = 'merc'#request.GET['SRS']
    #TIME = request.GET['TIME']
    try:
        elevation = [int(request.GET['ELEVATION'])]
    except:
        elevation = [0]

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
        nindex = list(tree.nearest((lon, lat, lon, lat),1, objects=True))
        selected_longitude, selected_latitude = tuple(nindex[0].bbox[:2])
        index = nindex[0].id
        tree.close()
    else:
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
    #print 'final time to complete haversine ' + str(timeobj.time() - totaltimer)

    try:
        TIME = request.GET["TIME"]
        if TIME == "":
            now = date.today().isoformat()
            TIME = now + "T00:00:00"#
    except:
        now = date.today().isoformat()
        TIME = now + "T00:00:00"#
    TIMES = TIME.split("/")
    for i in range(len(TIMES)):
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
            return nc.variables[var][t]
        else:
            # Expects 3d cell variables.
            if len(nc.variables[var].shape) == 3:
                return nc.variables[var][t, layer[0], ind]
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
        varis[0] = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in varis[0]]
        output_dict["time"] = {"units": "iso", "values": varis[0]}
        output_dict["latitude"] = {"units":"degrees_north", "values":float(selected_latitude)}
        output_dict["longitude"] = {"units":"degrees_east", "values":float(selected_longitude)}
        for i, var in enumerate(QUERY_LAYERS): # TODO: use map to convert to floats
            varis[i+1] = list(varis[i+1])
            for q, v in enumerate(varis[i+1]):
                if numpy.isnan(v):
                    varis[i+1][q] = float("nan")
                else:
                    varis[i+1][q] = float(varis[i+1][q])
            output_dict[var] = {"units": datasetnc.variables[var].units, "values": varis[i+1]}
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
                    thisline.append(varis[k][i])
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
'''
