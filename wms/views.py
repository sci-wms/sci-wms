import os
import json

from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.template.response import TemplateResponse
from django.core import serializers
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.cache import cache_page
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from wms.models import Dataset, Server, Variable
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


def demo(request):
    context = { 'datasets'  : Dataset.objects.all()}
    return render_to_response('wms/demo.html', context, context_instance=RequestContext(request))


def enhance_getmap_request(dataset, layer, request):
    gettemp = request.GET.copy()

    # 'time' parameter
    times = wms_handler.get_times(request)
    dimensions = wms_handler.get_dimensions(request)
    defaults = layer.defaults

    newgets = dict(
        starting=times.min,
        ending=times.max,
        time=wms_handler.get_time(request),
        crs=wms_handler.get_projection(request),
        bbox=wms_handler.get_bbox(request),
        wgs84_bbox=wms_handler.get_wgs84_bbox(request),
        colormap=wms_handler.get_colormap(request),
        colorscalerange=wms_handler.get_colorscalerange(request, defaults.min, defaults.max),
        elevation=wms_handler.get_elevation(request),
        width=dimensions.width,
        height=dimensions.height,
        image_type=wms_handler.get_imagetype(request),
        logscale=wms_handler.get_logscale(request, defaults.logscale),
        vectorscale=wms_handler.get_vectorscale(request)
    )
    gettemp.update(newgets)
    request.GET = gettemp

    # Check required parameters here and raise a ValueError if needed

    return request


def enhance_getlegendgraphic_request(dataset, layer, request):
    gettemp = request.GET.copy()

    dimensions = wms_handler.get_dimensions(request)
    defaults = layer.defaults

    newgets = dict(
        colorscalerange=wms_handler.get_colorscalerange(request, defaults.min, defaults.max),
        width=dimensions.width,
        height=dimensions.height,
        image_type=wms_handler.get_imagetype(request, parameter='style'),
        colormap=wms_handler.get_colormap(request, parameter='style'),
        format=wms_handler.get_format(request),
        showlabel=wms_handler.get_show_label(request),
        showvalues=wms_handler.get_show_values(request),
        units=wms_handler.get_units(request, layer.units),
        logscale=wms_handler.get_logscale(request, defaults.logscale),
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
        latitude=targets.latitude,
        longitude=targets.longitude,
        elevation=wms_handler.get_elevation(request),
        crs=crs,
        info_format=wms_handler.get_info_format(request)
    )
    gettemp.update(newgets)
    request.GET = gettemp
    return request


def enhance_getmetadata_request(dataset, layer, request):
    gettemp = request.GET.copy()

    # 'time' parameter
    dimensions = wms_handler.get_dimensions(request)

    newgets = dict(
        time=wms_handler.get_time(request),
        crs=wms_handler.get_projection(request),
        bbox=wms_handler.get_bbox(request),
        wgs84_bbox=wms_handler.get_wgs84_bbox(request),
        elevation=wms_handler.get_elevation(request),
        width=dimensions.width,
        height=dimensions.height,
        item=wms_handler.get_item(request)
    )
    gettemp.update(newgets)
    request.GET = gettemp
    return request


class DefaultsView(View):

    def get(self, request):
        defaults = Variable.objects.all()
        return TemplateResponse(request, 'wms/defaults.html', dict(defaults=defaults))


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
                elif reqtype.lower() == 'getmetadata':
                    request = enhance_getmetadata_request(dataset, layer, request)
                try:
                    response = getattr(dataset, reqtype.lower())(layer, request)
                except AttributeError as e:
                    logger.exception(e)
                    return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
                except NotImplementedError as e:
                    return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
                # Test formats, etc. before returning?
                return response
        except (AttributeError, ValueError) as e:
            logger.exception(str(e))
            return HttpResponse(str(e), status=500, reason="Could not process inputs", content_type="application/json")
        except NotImplementedError as e:
            logger.exception(str(e))
            return HttpResponse('"{}" is not implemented for a {}'.format(reqtype, dataset.__class__.__name__), status=500, reason="Could not process inputs", content_type="application/json")
