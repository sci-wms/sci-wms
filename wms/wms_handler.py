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
    xy = [None, None]
    x = request.GET.get('x')
    if x:
        xy[0] = float(x)
    y = request.GET.get('y')
    if y:
        xy[1] = float(y)

    return xy


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
        return DotDict(min=None, max=None)
