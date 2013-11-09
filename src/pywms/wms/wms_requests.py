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


import sys, os, gc, bisect, math, datetime, numpy, netCDF4, multiprocessing, logging, traceback
from pywms.wms.models import Dataset, Server, Group
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
import pywms.server_local_config as config

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def groupGetCapabilities(req, group, logger): # TODO move get capabilities to template system like sciwps
    """
    get capabilities document based on this getcaps:

    http://coastmap.com/ecop/wms.aspx?service=WMS&version=1.1.1&request=getcapabilities

    """
    
    datasets = list(Dataset.objects.filter(group=group))
    
    
    # Create the object to be encoded to xml later
    root = ET.Element('WMT_MS_Capabilities')
    root.attrib["version"] = "1.1.1"#request.GET["version"]
    href = "http://" + Site.objects.values()[0]['domain'] + "/" + group.name + "/?" # must encode spaces here

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
    #ET.SubElement(layer, "Title").text =  Dataset.objects.get(name=dataset).title
    ET.SubElement(layer, "Title").text = group.name
    #ET.SubElement(layer, "Abstract").text =  Dataset.objects.get(name=dataset).abstract
    ET.SubElement(layer, "Abstract").text = group.abstract
    ET.SubElement(layer, "SRS").text =  "EPSG:3857"
    ET.SubElement(layer, "SRS").text =  "MERCATOR"
    for dataset in datasets:
        #nc = netCDF4.Dataset(Dataset.objects.get(name=dataset).uri)
        nc = netCDF4.Dataset(dataset.uri)
        topology = netCDF4.Dataset(os.path.join(config.topologypath, dataset.name + '.nc'))
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
                ET.SubElement(layer1, "Name").text = dataset.name + "/" + variable
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
                ET.SubElement(layer1, "SRS").text = "EPSG:3857"
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
