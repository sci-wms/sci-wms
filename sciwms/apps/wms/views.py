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
import gc
import sys
import json
import ast
import urllib
import bisect
import logging
import datetime
import traceback
import subprocess
import multiprocessing
import time as timeobj
from urlparse import urlparse
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import numpy
import netCDF4

# Import from matplotlib and set backend
import matplotlib
matplotlib.use("Agg")
from mpl_toolkits.basemap import Basemap
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Other random "from" imports
from rtree import index as rindex
from collections import deque
from StringIO import StringIO  # will be deprecated in Python3, use io.byteIO instead

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.contrib.auth import authenticate, login, logout

from sciwms.libs.data import cgrid, ugrid
import sciwms.apps.wms.wms_requests as wms_reqs
from sciwms.apps.wms.models import Dataset, Server, Group, VirtualLayer
from sciwms.apps.wms import logger


def crossdomain(request):
    with open(os.path.join(settings.COMMON_STATIC_FILES, "common", "crossdomain.xml")) as f:
        response = HttpResponse(content_type="text/xml")
        response.write(f.read())
    return response


def datasets(request):
    from django.core import serializers
    datasets = Dataset.objects.all()
    data = serializers.serialize('json', datasets)
    return HttpResponse(data, mimetype='application/json')


def grouptest(request, group):
    from django.template import Context
    sites = Site.objects.values()
    #print group
    group = Group.objects.get(name=group)
    dict1 = Context({ 'localsite' : sites[0]['domain'],
                      'datasets'  : list(Dataset.objects.filter(group=group))})
    return HttpResponse(get_template('wms/wms_openlayers_test.html').render(dict1))


def groups(request, group):
    import django.shortcuts as dshorts
    reqtype = None
    try:
        reqtype = request.GET['REQUEST']
    except:
        try:
            reqtype = request.GET['request']
        except:
            group = Group.objects.get(name=group)
            datasets = Dataset.objects.filter(group=group)
            for dataset in datasets:
                dataset.uri = dataset.path()
                if urlparse(dataset.uri).scheme != "":
                    # Used in template to linkify to URI
                    dataset.online = True
            context = { "datasets" : datasets }
            return dshorts.render_to_response('wms/index.html', context)
    if reqtype.lower() == "getcapabilities":  # Do GetCapabilities
        group = Group.objects.get(name=group)
        caps = wms_reqs.groupGetCapabilities(request, group, logger)
        return caps
    elif reqtype is not None:
        try:
            layers = request.GET["LAYERS"]
        except:
            layers = request.GET["layers"]
        dataset = layers.split("/")[0]
        request.GET = request.GET.copy()
        request.GET["LAYERS"] = layers.replace(dataset+"/", "")
        request.GET["layers"] = layers.replace(dataset+"/", "")
        return wms(request, dataset)


def index(request):
    import django.shortcuts as dshorts
    datasets = Dataset.objects.all()
    for dataset in datasets:
        dataset.uri = dataset.path()
        if urlparse(dataset.uri).scheme != "":
            # Used in template to linkify to URI
            dataset.online = True
    context = { "datasets" : datasets }
    return dshorts.render_to_response('wms/index.html', context)


def openlayers(request, filepath):
    return HttpResponse(get_template('wms/openlayers/%s' % filepath, content_type='text'))


def simpleclient(request):
    #grid_cache.check_topology_age()
    from django.template import Context
    sites = Site.objects.values()
    dict1 = Context({ 'localsite' : sites[0]['domain'],
                      'datasets'  : Dataset.objects.values()})
    return HttpResponse(get_template('wms/wms_openlayers_test.html').render(dict1))


def leafletclient(request):
    from django.template import Context
    sites = Site.objects.values()
    dict1 = Context({ 'localsite' : sites[0]['domain'],
                      'datasets'  : Dataset.objects.values()})
    return HttpResponse(get_template('wms/leaflet_example.html').render(dict1))


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
            return HttpResponse(json.dumps({ "message" : "Please include 'dataset' parameter in GET request." }), mimetype='application/json')
        else:
            d = Dataset.objects.get(name=dataset)
            d.update_cache(force=True)
            return HttpResponse(json.dumps({ "message" : "Scheduled" }), mimetype='application/json')
    else:
        return HttpResponse(json.dumps({ "message" : "Authentication failed, please login to the admin console first or pass login credentials to the GET request ('username' and 'password')" }), mimetype='application/json')

    logout_view(request)

def add(request):
    # some hijacking of django's default behavior to get this to work
    # this functions will be gradually taken over by the wmsrest app
    if len(request.POST) < 1:
        request_body = request.body
        body = ast.literal_eval(request_body)
        encoded_body = urllib.urlencode(body)
        request.POST = QueryDict(encoded_body)
    if authenticate_view(request):
        dataset_endpoint = request.POST.get("uri", None)
        dataset_name = request.POST.get("name", None)
        dataset_title = request.POST.get("title", None)
        dataset_abstract = request.POST.get("abstract", None)
        dataset_update = bool(request.POST.get("update", False))
        memberof_groups = request.POST.get("groups", None)
        if memberof_groups is None:
            memberof_groups = []
        else:
            memberof_groups = memberof_groups.split(",")
        if dataset_name is None:
            return HttpResponse("Exception: Please include 'id' parameter in POST request.", status=500)
        elif dataset_endpoint is None:
            return HttpResponse("Exception: Please include 'uri' parameter in POST request.", status=500)
        elif dataset_abstract is None:
            return HttpResponse("Exception: Please include 'abstract' parameter in POST request.", status=500)
        elif dataset_update is None:
            return HttpResponse("Exception: Please include 'update' parameter in POST request.", status=500)
        else:
            try:
                dataset = Dataset.objects.get(name=dataset_name)
            except Dataset.DoesNotExist:
                dataset = Dataset.objects.create(name=dataset_name,
                                                 title=dataset_title,
                                                 abstract=dataset_abstract,
                                                 uri=dataset_endpoint,
                                                 keep_up_to_date=dataset_update)
                dataset.save()
            for groupname in memberof_groups:
                if len(list(Group.objects.filter(name=groupname))) > 0:
                    try:
                        group = Group.objects.get(name=groupname)
                        dataset.groups.add(group)
                    except Group.DoesNotExist:
                        pass
                dataset.save()
            return HttpResponse("Success: Dataset %s added to the server, and to %s groups." % (dataset.pk, memberof_groups.__str__()))
    else:
        return HttpResponse("Not authenticated")
    logout_view(request)


def add_to_group(request):
    if authenticate_view(request):
        dataset_id = request.GET.get("id", None)
        memberof_groups = request.GET.get("groups", None)
        if memberof_groups is None:
            memberof_groups = []
        else:
            memberof_groups = memberof_groups.split(",")
        if dataset_id is None:
            return HttpResponse("Exception: Please include 'id' parameter in POST request.", status=500)
        else:
            if len(list(Dataset.objects.filter(name=dataset_id))) > 0:
                dataset = Dataset.objects.get(name = dataset_id)
            else:
                return HttpResponse("Exception: Dataset matching that ID (%s) does not exist." % (dataset_id,), status=500)
            for groupname in memberof_groups:
                if len(list(Group.objects.filter(name = groupname))) > 0:
                    group = Group.objects.get(name = groupname)
                    dataset.groups.add(group)
                    dataset.save()
                return HttpResponse("Success: Dataset %s added to %s groups." % (dataset_id, memberof_groups.__str__()))
    logout_view(request)


def remove(request):
    if authenticate_view(request):
        dataset_id = request.GET.get("id", None)
        if dataset_id is None:
            return HttpResponse("Exception: Please include 'id' parameter in GET request.")
        else:
            dataset = Dataset.objects.get(name=dataset_id)
            dataset.delete()
            return HttpResponse("Dataset %s removed from this wms server." % dataset_id)
    else:
        return HttpResponse(json.dumps({ "message" : "authentication failed" }), mimetype='application/json')
    logout_view(request)


def remove_from_group(request):
    if authenticate_view(request):
        dataset_id = request.GET.get("id", None)
        memberof_groups = request.GET.get("groups", None)
        if memberof_groups is None:
            memberof_groups = []
        else:
            memberof_groups = memberof_groups.split(",")
            if dataset_id is None:
                return HttpResponse("Exception: Please include 'id' parameter in POST request.", status=500)
            else:
                if len(list(Dataset.objects.filter(name=dataset_id))) > 0:
                    dataset = Dataset.objects.get(name = dataset_id)
                else:
                    return HttpResponse("Exception: Dataset matching that ID (%s) does not exist." % (dataset_id,), status=500)
            for groupname in memberof_groups:
                if len(list(Group.objects.filter(name = groupname))) > 0:
                    group = Group.objects.get(name = groupname)
                    dataset.groups.remove(group)
                    dataset.save()
            return HttpResponse()
    logout_view(request)


def documentation(request):
    return HttpResponseRedirect('http://acrosby.github.io/sci-wms')


def normalize_get_params(request):
    gettemp = request.GET.copy()
    for key in request.GET.iterkeys():
        gettemp[key.lower()] = request.GET[key]
    request.GET = gettemp
    return request


def database_request_interaction(request, dataset):
    if VirtualLayer.objects.filter(datasets__name = dataset):
        vlayer = VirtualLayer.objects.filter(datasets__name=dataset).filter(layer_expression = request.GET['layers'])
        request.GET['layers'] = vlayer[0].layer_expression
    return request


def wms(request, dataset):
    try:
        request = normalize_get_params(request)
        reqtype = request.GET['request']
        if reqtype.lower() == 'getmap':
            request = database_request_interaction(request, dataset)
            import sciwms.apps.wms.wms_handler as wms
            handler = wms.wms_handler(request)
            action_request = handler.make_action_request(request)
            if action_request is not None:
                response = getMap(action_request, dataset)
            else:
                response = HttpResponse()
        elif reqtype.lower() == 'getfeatureinfo':
            response = getFeatureInfo(request, dataset)
        elif reqtype.lower() == 'getlegendgraphic':
            response = getLegendGraphic(request, dataset)
        elif reqtype.lower() == 'getcapabilities':
            response = getCapabilities(request, dataset)
        logger.info(str(request.GET))
        return response
    except Exception:
        raise
        exc_type, exc_value, exc_traceback = sys.exc_info()
        str_exc_descr = repr(traceback.format_exception(exc_type, exc_value, exc_traceback)) + '\n' + str(request)
        logger.error("Status 500 Error: " + str_exc_descr)
        return HttpResponse("<pre>Error: " + str_exc_descr + "</pre>", status=500)


def getCapabilities(req, dataset):  # TODO move get capabilities to template system like sciwps
    """
    get capabilities document based on this getcaps:


    http://coastmap.com/ecop/wms.aspx?service=WMS&version=1.1.1&request=getcapabilities

    """

    dataset = Dataset.objects.get(name=dataset)

    # Create the object to be encoded to xml later
    root = ET.Element('WMT_MS_Capabilities')
    root.attrib["version"] = "1.1.1"
    href = "http://" + Site.objects.values()[0]['domain'] + "/wms/" + dataset.name + "/?"
    virtual_layers = VirtualLayer.objects.filter(datasets__name=dataset.name)
    expected_configurations = {"u"       : ("u,v", ","),
                               "u-vel"   : ("u-vel,v-vel", ","),
                               "ua"      : ("ua,va", ","),
                               "U"       : ("U,V", ","),
                               "uc"      : ("uc,vc", ","),
                               "air_u"   : ("air_u,air_v", ","),
                               "water_u" : ("water_u,water_v", ",")
                              }
    virtual_configurations = {}
    for layer in list(virtual_layers):
        if "*" in layer.layer_expression:
            virtual_configurations[layer.layer_expression.split("*")[0]] = (layer.layer, "*")
        elif "+" in layer.layer_expression:
            virtual_configurations[layer.layer_expression.split("+")[0]] = (layer.layer, "+")
        elif "," in layer.layer_expression:
            virtual_configurations[layer.layer_expression.split(",")[0]] = (layer.layer, ",")

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
    ET.SubElement(layer, "Title").text      = dataset.title
    ET.SubElement(layer, "Abstract").text   = dataset.abstract
    ET.SubElement(layer, "SRS").text        = "EPSG:3857"
    ET.SubElement(layer, "SRS").text        = "MERCATOR"

    nc = netCDF4.Dataset(dataset.path())
    topology = netCDF4.Dataset(dataset.topology_file)
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
        if True:
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
            ET.SubElement(layer1, "SRS").text = "EPSG:3857"
            llbbox = ET.SubElement(layer1, "LatLonBoundingBox")
            templon = topology.variables["lon"][:]
            templat = topology.variables["lat"][:]
            #templon = templon[not numpy.isnan(templon)]
            #templat = templat[not numpy.isnan(templat)]
            llbbox.attrib["minx"] = str(numpy.nanmin(templon))
            llbbox.attrib["miny"] = str(numpy.nanmin(templat))
            llbbox.attrib["maxx"] = str(numpy.nanmax(templon))
            llbbox.attrib["maxy"] = str(numpy.nanmax(templat))
            #llbbox.attrib["minx"] = str(templon.min())
            #llbbox.attrib["miny"] = str(templat.min())
            #llbbox.attrib["maxx"] = str(templon.max())
            #llbbox.attrib["maxy"] = str(templat.max())
            llbbox = ET.SubElement(layer1, "BoundingBox")
            llbbox.attrib["SRS"] = "EPSG:4326"
            #llbbox.attrib["minx"] = str(templon.min())
            #llbbox.attrib["miny"] = str(templat.min())
            #llbbox.attrib["maxx"] = str(templon.max())
            #llbbox.attrib["maxy"] = str(templat.max())
            llbbox.attrib["minx"] = str(numpy.nanmin(templon))
            llbbox.attrib["miny"] = str(numpy.nanmin(templat))
            llbbox.attrib["maxx"] = str(numpy.nanmax(templon))
            llbbox.attrib["maxy"] = str(numpy.nanmax(templat))
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
                try:
                    units = topology.variables["time"].units
                #print units
                #print topology.variables["time"][0], len(topology.variables["time"])
                #print topology.variables["time"][-1]
                    if len(topology.variables["time"]) == 1:
                        time_extent.text = netCDF4.num2date(topology.variables["time"][0], units).isoformat('T') + "Z"
                    else:
                        if dataset.display_all_timesteps:
                            temptime = [netCDF4.num2date(topology.variables["time"][i], units).isoformat('T')+"Z" for i in xrange(topology.variables["time"].shape[0])]
                            time_extent.text = temptime.__str__().strip("[]").replace("'", "").replace(" ", "")
                        else:
                            time_extent.text = netCDF4.num2date(topology.variables["time"][0], units).isoformat('T') + "Z/" + netCDF4.num2date(topology.variables["time"][-1], units).isoformat('T') + "Z"
                except:
                    if len(topology.variables["time"]) == 1:
                        time_extent.text = str(topology.variables["time"][0])
                    else:
                        time_extent.text = str(topology.variables["time"][0]) + "/" + str(topology.variables["time"][-1])
            except:
                pass
            ## Listing all available elevation layers is a tough thing to do for the range of types of datasets...
            if topology.grid.lower() == 'false':
                if nc.variables[variable].ndim > 2:
                    try:
                        ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables["siglay"].shape[0])).replace("[", "").replace("]", "").replace(" ", "")
                        elev_extent.text = str(range(nc.variables["siglay"].shape[0])).replace("[", "").replace("]", "").replace(" ", "")
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
            elif topology.grid.lower() == 'cgrid':
                if nc.variables[variable].ndim > 3:
                    try:
                        ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables[variable].shape[1])).replace("[", "").replace("]", "").replace(" ", "")
                        elev_extent.text = str(range(nc.variables[variable].shape[1])).replace("[", "").replace("]", "").replace(" ", "")
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
            for configurations in [expected_configurations, virtual_configurations]:
                if variable in configurations:
                    layername, layertype = configurations[variable]
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
                    ET.SubElement(layer1, "Title").text = layername  # current velocity (u,v)"
                    if layertype == "*":
                        typetext = "3 band true color composite"
                    elif layertype == "+":
                        typetext = "sum or addition of two layers"
                    elif layertype == ",":
                        typetext = "magnitude or vector layer"
                    ET.SubElement(layer1, "Abstract").text = "Virtual Layer, "+typetext  # "Magnitude of current velocity from u and v components"
                    ET.SubElement(layer1, "SRS").text = "EPSG:4326"
                    llbbox = ET.SubElement(layer1, "LatLonBoundingBox")
                    llbbox.attrib["minx"] = str(numpy.nanmin(templon))
                    llbbox.attrib["miny"] = str(numpy.nanmin(templat))
                    llbbox.attrib["maxx"] = str(numpy.nanmax(templon))
                    llbbox.attrib["maxy"] = str(numpy.nanmax(templat))
                    llbbox = ET.SubElement(layer1, "BoundingBox")
                    llbbox.attrib["SRS"] = "EPSG:4326"
                    llbbox.attrib["minx"] = str(numpy.nanmin(templon))
                    llbbox.attrib["miny"] = str(numpy.nanmin(templat))
                    llbbox.attrib["maxx"] = str(numpy.nanmax(templon))
                    llbbox.attrib["maxy"] = str(numpy.nanmax(templat))
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
                        if dataset.display_all_timesteps:
                            temptime = [netCDF4.num2date(topology.variables["time"][i], units).isoformat('T')+"Z" for i in xrange(topology.variables["time"].shape[0])]
                            time_extent.text = temptime.__str__().strip("[]").replace("'", "").replace(" ", "")
                        else:
                            time_extent.text = netCDF4.num2date(topology.variables["time"][0], units).isoformat('T') + "Z/" + netCDF4.num2date(topology.variables["time"][-1], units).isoformat('T') + "Z"
                    except:
                        time_extent.text = str(topology.variables["time"][0]) + "/" + str(topology.variables["time"][-1])
                    if nc.variables[variable].ndim > 2:
                        try:
                            ET.SubElement(layer1, "DepthLayers").text = str(range(nc.variables["siglay"].shape[0])).replace("[", "").replace("]", "")
                            elev_extent.text = str(range(nc.variables["siglay"].shape[0])).replace("[", "").replace("]", "")
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
                    if layertype == "*":
                        style = "composite"
                        style_code = style + "_average_jet_None_None_" + location + "_False"
                        style = ET.SubElement(layer1, "Style")
                        ET.SubElement(style, "Name").text = style_code
                        ET.SubElement(style, "Title").text = style_code
                        ET.SubElement(style, "Abstract").text = "http://" + Site.objects.values()[0]['domain'] + "/doc"
                        legendurl = ET.SubElement(style, "LegendURL")
                        legendurl.attrib["width"] = "50"
                        legendurl.attrib["height"] = "80"
                        ET.SubElement(legendurl, "Format").text = "image/png"
                    elif layertype == "+":
                        for style in ["pcolor", "facets", "filledcontours", "contours"]:
                            style_code = style + "_average_jet_None_None_" + location + "_False"
                            style = ET.SubElement(layer1, "Style")
                            ET.SubElement(style, "Name").text = style_code
                            ET.SubElement(style, "Title").text = style_code
                            ET.SubElement(style, "Abstract").text = "http://" + Site.objects.values()[0]['domain'] + "/doc"
                            legendurl = ET.SubElement(style, "LegendURL")
                            legendurl.attrib["width"] = "50"
                            legendurl.attrib["height"] = "80"
                            ET.SubElement(legendurl, "Format").text = "image/png"
                    elif layertype == ",":
                        for style in ["vectors", "barbs", "pcolor", "facets", "filledcontours", "contours"]:
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
        if True:  # except:
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
            output_str = callback + "(" + json.dumps(output_dict, indent=4, separators=(',', ': '), allow_nan=True) + ")"
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
    styles = request.GET["styles"].split("_")
    try:
        climits = (float(styles[3]), float(styles[4]))
    except:
        climits = (None, None)
    variables = request.GET["layer"].split(",")
    plot_type = styles[0]
    colormap = styles[2].replace('-', '_')

    # direct the service to the dataset
    # make changes to server_local_config.py
    if settings.LOCALDATASET:
        url = settings.LOCALDATASETPATH[dataset]
    else:
        url = Dataset.objects.get(name=dataset).path()
    nc = netCDF4.Dataset(url)

    """
    Create figure and axes for small legend image
    """
    #from matplotlib.figure import Figure
    from matplotlib.pylab import get_cmap
    fig = Figure(dpi=100., facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figwidth(1*1.3)
    fig.set_figheight(1.5*1.3)

    """
    Create the colorbar or legend and add to axis
    """
    try:
        units = nc.variables[variables[0]].units
    except:
        units = ''
    if climits[0] is None or climits[1] is None:  # TODO: NOT SUPPORTED RESPONSE
            #going to have to get the data here to figure out bounds
            #need elevation, bbox, time, magnitudebool
            CNorm = None
            ax = fig.add_axes([0, 0, 1, 1])
            ax.grid(False)
            ax.text(.5, .5, 'Error: No Legend\navailable for\nautoscaled\ncolor styles!', ha='center', va='center', transform=ax.transAxes, fontsize=8)
    elif plot_type not in ["contours", "filledcontours"]:
        #use limits described by the style
        ax = fig.add_axes([.01, .05, .2, .8])  # xticks=[], yticks=[])
        CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                            vmax=climits[1],
                                            clip=False,
                                            )
        cb = matplotlib.colorbar.ColorbarBase(ax,
                                              cmap=get_cmap(colormap),
                                              norm=CNorm,
                                              orientation='vertical',
                                              )
        cb.set_label(units)
    else:  # plot type somekind of contour
        if plot_type == "contours":
            #this should perhaps be a legend...
            #ax = fig.add_axes([0,0,1,1])
            fig_proxy = Figure(frameon=False, facecolor='none', edgecolor='none')
            ax_proxy = fig_proxy.add_axes([0, 0, 1, 1])
            CNorm = matplotlib.colors.Normalize(vmin=climits[0], vmax=climits[1], clip=True)
            #levs = numpy.arange(0, 12)*(climits[1]-climits[0])/10
            levs = numpy.linspace(climits[0], climits[1], 11)
            x, y = numpy.meshgrid(numpy.arange(10), numpy.arange(10))
            cs = ax_proxy.contourf(x, y, x, levels=levs, norm=CNorm, cmap=get_cmap(colormap))

            proxy = [plt.Rectangle((0, 0), 0, 0, fc=pc.get_facecolor()[0]) for pc in cs.collections]

            fig.legend(proxy, levs,
                       #bbox_to_anchor = (0, 0, 1, 1),
                       #bbox_transform = fig.transFigure,
                       loc = 6,
                       title = units,
                       prop = { 'size' : 8 },
                       frameon = False,
                       )
        elif plot_type == "filledcontours":
            #this should perhaps be a legend...
            #ax = fig.add_axes([0,0,1,1])
            fig_proxy = Figure(frameon=False, facecolor='none', edgecolor='none')
            ax_proxy = fig_proxy.add_axes([0, 0, 1, 1])
            CNorm = matplotlib.colors.Normalize(vmin=climits[0], vmax=climits[1], clip=False,)
            #levs = numpy.arange(1, 12)*(climits[1]-(climits[0]))/10
            levs = numpy.linspace(climits[0], climits[1], 10)
            levs = numpy.hstack(([-99999], levs, [99999]))

            x, y = numpy.meshgrid(numpy.arange(10), numpy.arange(10))
            cs = ax_proxy.contourf(x, y, x, levels=levs, norm=CNorm, cmap=get_cmap(colormap))

            proxy = [plt.Rectangle((0, 0), 0, 0, fc=pc.get_facecolor()[0]) for pc in cs.collections]

            levels = []
            for i, value in enumerate(levs):
                #if i == 0:
                #    levels[i] = "<" + str(value)
                if i == len(levs)-2 or i == len(levs)-1:
                    levels.append("> " + str(value))
                elif i == 0:
                    levels.append("< " + str(levs[i+1]))
                else:
                    #levels.append(str(value) + "-" + str(levs[i+1]))
                    text = '%.2f-%.2f' % (value, levs[i+1])
                    levels.append(text)
            logger.info( str((levels, levs)) )
            fig.legend(proxy, levels,
                       #bbox_to_anchor = (0, 0, 1, 1),
                       #bbox_transform = fig.transFigure,
                       loc = 6,
                       title = units,
                       prop = { 'size' : 6 },
                       frameon = False,
                       )

    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    nc.close()
    return response


def getFeatureInfo(request, dataset):
    """
     /wms/GOM3/?ELEVATION=1&LAYERS=temp&FORMAT=image/png&TRANSPARENT=TRUE&STYLES=facets_average_jet_0_32_node_False&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&SRS=EPSG:3857&BBOX=-7949675.196111,5078194.822174,-7934884.63114,5088628.476533&X=387&Y=196&INFO_FORMAT=text/csv&WIDTH=774&HEIGHT=546&QUERY_LAYERS=salinity&TIME=2012-08-14T00:00:00/2012-08-16T00:00:00
    """
    from datetime import date
    from mpl_toolkits.basemap import pyproj

    dataset = Dataset.objects.get(name=dataset)

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
    gridtype = topology.grid

    if gridtype == u'False':
        test_index = 0
        if 'node' in styles:
            tree = rindex.Index(dataset.node_tree_index_file)
            #lats = topology.variables['lat'][:]
            #lons = topology.variables['lon'][:]
            nindex = list(tree.nearest((lon, lat, lon, lat), 1, objects=True))
        else:
            from shapely.geometry import Polygon, Point
            tree = rindex.Index(dataset.cell_tree_index_file)
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
        tree = rindex.Index(dataset.node_tree_index_file)
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

    url = dataset.path()
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


def getMap(request, dataset):
    '''
    the meat and bones of getMap
    '''
    from mpl_toolkits.basemap import pyproj
    from matplotlib.figure import Figure

    #totaltimer = timeobj.time()
    #loglist = []

    # direct the service to the dataset
    dataset = Dataset.objects.get(name=dataset)
    url = dataset.path()

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
    for i, l in enumerate(layer):
    #    layer[i] = int(l)-1
        layer = int(l)
    layer = numpy.asarray(layer)
    actions = request.GET["actions"]
    actions = set(actions.split(","))

    # Get the colormap requested, the color limits/scaling
    colormap = request.GET["colormap"]
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

    if "kml" in actions:  # TODO: REMOVE THIS!
        pass
    else:
        # Open topology cache file, and the actualy data endpoint
        topology = netCDF4.Dataset(dataset.topology_file)
        datasetnc = netCDF4.Dataset(url)
        gridtype = topology.grid  # Grid type found in topology file
        logger.info("gridtype: " + gridtype)
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
                #wher = numpy.where(lon<lonmin)
                if gridtype != 'False':
                    lon[lon < 0] = lon[lon < 0] + 360
                else:
                    lon[lon < lonmin] = lon[lon < lonmin] + 360
            else:
                lon = topology.variables[toplonc][:]
            lat = topology.variables[toplatc][:]
            if gridtype != 'False':
                if gridtype == 'cgrid':
                    index, lat, lon = cgrid.subset(latmin, lonmin, latmax, lonmax, lat, lon)
            else:
                index, lat, lon = ugrid.subset(latmin, lonmin, latmax, lonmax, lat, lon)

        if index is not None:
            if ("facets" in actions) or \
               ("regrid" in actions) or \
               ("shape" in actions) or \
               ("contours" in actions) or \
               ("interpolate" in actions) or \
               ("filledcontours" in actions) or \
               ("pcolor" in actions) or \
               (topology_type.lower() == 'node'):
                if gridtype == 'False':  # If ugrid
                    # If the nodes are important, get the node coords, and
                    # topology array
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
                    pass  # If regular grid, do nothing
            else:
                nv = None
                lonn, latn = None, None

            times = topology.variables['time'][:]
            datestart = datetime.datetime.strptime(datestart, "%Y-%m-%dT%H:%M:%S" )  # datestr --> datetime obj
            datestart = round(netCDF4.date2num(datestart, units=topology.variables['time'].units))  # datetime obj --> netcdf datenum
            time = bisect.bisect_right(times, datestart) - 1
            if settings.LOCALDATASET:
                time = [1]
            elif time == -1:
                time = [0]
            else:
                time = [time]
            if dateend != datestart:
                dateend = datetime.datetime.strptime( dateend, "%Y-%m-%dT%H:%M:%S" )  # datestr --> datetime obj
                dateend = round(netCDF4.date2num(dateend, units=topology.variables['time'].units))  # datetime obj --> netcdf datenum
                time.append(bisect.bisect_right(times, dateend) - 1)
                if settings.LOCALDATASET:
                    time[1] = 1
                elif time[1] == -1:
                    time[1] = 0
                else:
                    time[1] = time[1]
                time = range(time[0], time[1]+1)
            t = time  # TODO: ugh this is bad
            #loglist.append('time index requested ' + str(time))

            # Get the data and appropriate resulting shape from the data source
            if gridtype == 'False':
                var1, var2 = ugrid.getvar(datasetnc, t, layer, variables, index)
            if gridtype == 'cgrid':
                index = numpy.asarray(index)
                var1, var2 = cgrid.getvar(datasetnc, t, layer, variables, index)

            if latmin != latmax:  # TODO: REMOVE THIS CHECK ALREADY DONE ABOVE
                if gridtype == 'False':  # TODO: Should take a look at this
                    # This is averaging in time over all timesteps downloaded
                    if "composite" in actions:
                        pass
                    elif "average" in actions:
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
                    elif "maximum" in actions:
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
                try:  # Fail gracefully if not standard_name, should do this a little better than a try
                    if 'direction' in datasetnc.variables[variables[1]].standard_name:
                        #assign new var1,var2 as u,v components
                        var2 = 450 - var2
                        var2[var2 > 360] = var2[var2 > 360] - 360
                        origvar2 = var2
                        var2 = numpy.sin(numpy.radians(origvar2)) * var1  # var 2 needs to come first so that
                        var1 = numpy.cos(numpy.radians(origvar2)) * var1  # you arn't multiplying by the wrong var1 val
                except:
                    pass

                # Close remote dataset and local cache
                topology.close()
                datasetnc.close()

                if (climits[0] == "None") or (climits[1] == "None"):
                    if magnitude.lower() == "log":
                        CNorm = matplotlib.colors.LogNorm()
                    else:
                        CNorm = matplotlib.colors.Normalize()
                else:
                    if magnitude.lower() == "log":
                        CNorm = matplotlib.colors.LogNorm(vmin=climits[0],
                                                          vmax=climits[1],
                                                          clip=True,
                                                         )
                    else:
                        CNorm = matplotlib.colors.Normalize(vmin=climits[0],
                                                            vmax=climits[1],
                                                            clip=True,
                                                           )
                # Plot to the projected figure axes!
                if gridtype == 'cgrid':
                    lon, lat = m(lon, lat)
                    cgrid.plot(lon, lat, var1, var2, actions, m.ax, fig,
                               aspect = m.aspect,
                               height = height,
                               width = width,
                               norm = CNorm,
                               cmin = climits[0],
                               cmax = climits[1],
                               magnitude = magnitude,
                               cmap = colormap,
                               basemap = m,
                               lonmin = lonmin,
                               latmin = latmin,
                               lonmax = lonmax,
                               latmax = latmax,
                               projection = projection)
                elif gridtype == 'False':
                    fig, m = ugrid.plot(lon, lat, lonn, latn, nv, var1, var2, actions, m, m.ax, fig,
                                        aspect = m.aspect,
                                        height = height,
                                        width = width,
                                        norm = CNorm,
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
                                        projection = projection)
                lonmax, latmax = m(lonmax, latmax)
                lonmin, latmin = m(lonmin, latmin)
                m.ax.set_xlim(lonmin, lonmax)
                m.ax.set_ylim(latmin, latmax)
                m.ax.set_frame_on(False)
                m.ax.set_clip_on(False)
                m.ax.set_position([0, 0, 1, 1])
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
            ax.set_position([0, 0, 1, 1])
            canvas = FigureCanvasAgg(fig)
            response = HttpResponse(content_type='image/png')
            canvas.print_png(response)

    gc.collect()
    #loglist.append('final time to complete request ' + str(timeobj.time() - totaltimer))
    #logger.info(str(loglist))
    return response
