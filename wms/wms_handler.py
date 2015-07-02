# -*- coding: utf-8 -*-
from datetime import datetime, date

import pyproj
from dateutil.parser import parse

from wms.utils import DotDict

from wms import logger


def get_bbox(request):
    """
    Return the [lonmin, latmin, lonmax, lonmax] - [lower (x,y), upper(x,y)]
    Units will be specified by projection.
    """
    elements = [ float(el) for el in request.GET["bbox"].split(",") ]
    return DotDict(minx=elements[0], miny=elements[1], maxx=elements[2], maxy=elements[3])


def get_wgs84_bbox(request):
    """
    Return the [lonmin, latmin, lonmax, lonmax] - [lower (x,y), upper(x,y)]
    in WGS84
    """
    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    crs = get_projection(request)
    bbox = get_bbox(request)

    wgs84_minx, wgs84_miny = pyproj.transform(crs, EPSG4326, bbox.minx, bbox.miny)
    wgs84_maxx, wgs84_maxy = pyproj.transform(crs, EPSG4326, bbox.maxx, bbox.maxy)

    return DotDict(minx=wgs84_minx, miny=wgs84_miny, maxx=wgs84_maxx, maxy=wgs84_maxy)


def get_info_format(request):
    """
    Return the INFO_FORMAT for GetFeatureInfo requests
    """
    try:
        return request.GET['info_format'].lower()
    except KeyError:
        return None


def get_projection(request):
    """
    Return the projection string passed into the request.
    Can be specified by \"SRS\" or \"CRS\" key (string).
    If \"SRS\" or \"CRS\" is not available, default to mercator.
    """
    projstr = request.GET.get("srs")
    if not projstr:
        projstr = request.GET.get("crs")

    if not projstr:
        projstr = "EPSG:3857"
        logger.debug("SRS or CRS no available in requst, defaulting to EPSG:3857 (mercator)")

    return pyproj.Proj(init=projstr)


def get_xy(request):
    """
    Returns list of floats
    """
    try:
        x = float(request.GET.get('x'))
    except ValueError:
        x = None

    try:
        y = float(request.GET.get('y'))
    except ValueError:
        y = None

    return DotDict(x=x, y=y)


def get_elevation(request):
    """
    Return the elevation
    """
    try:
        elev = request.GET["elevation"]
        return float(elev)
    except (TypeError, KeyError):
        return 0


def get_time(request):
    """
    Return the min and max times
    """
    time = request.GET.get('time')
    if time is None:
        return datetime.utcnow()
    else:
        return parse(time)


def get_times(request):
    """
    Return the min and max times
    """
    time = request.GET.get('time')
    if not time:
        time = date.today().isoformat() + "T00:00:00"
    times = sorted([ parse(t) for t in time.split("/") ])
    return DotDict(min=times[0], max=times[-1])


def get_colormap(request):
    try:
        return request.GET.get('styles').split(',')[0].split('_')[1]
    except (AttributeError, TypeError):
        return 'jet'


def get_imagetype(request):
    try:
        return request.GET.get('styles').split(',')[0].split('_')[0].lower()
    except (AttributeError, TypeError):
        return 'filledcontours'


def get_colorscalerange(request, default_min, default_max):
    try:
        climits = sorted([ float(x) for x in request.GET.get('colorscalerange').split(',') ])
        return DotDict(min=climits[0], max=climits[-1])
    except (AttributeError, TypeError):
        return DotDict(min=default_min, max=default_max)


def get_dimensions(request):
    """
    Return width and height of requested view.
    RETURNS width, height request should be in pixel units.
    """
    try:
        width = float(request.GET.get("width"))
        height = float(request.GET.get("height"))
        return DotDict(width=width, height=height)
    except:
        return DotDict(width=None, height=None)


def get_gfi_positions(xy, bbox, crs, dims):
    """ Returns the latitude and longitude the GFI should be performed at"""
    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    lon, lat = pyproj.transform(crs, EPSG4326, bbox.minx+((bbox.maxx-bbox.minx)*(xy.x/dims.width)), bbox.maxy-((bbox.maxy-bbox.miny)*(xy.y/dims.height)))
    return DotDict(latitude=lat, longitude=lon)
