# -*- coding: utf-8 -*-
from datetime import datetime, date

from dateutil.parser import parse
from dateutil.tz import tzutc
import pyproj

from wms.utils import DotDict, split, tz_aware_to_native

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

    return DotDict(minx=wgs84_minx, miny=wgs84_miny, maxx=wgs84_maxx, maxy=wgs84_maxy, bbox=(wgs84_minx, wgs84_miny, wgs84_maxx, wgs84_maxy))


def get_format(request):
    """
    Return the FORMAT for GetLegendGraphic requests
    """
    try:
        return 'image/png'  # request.GET['format'].lower()
    except KeyError:
        return 'image/png'


def get_show_label(request):
    """
    Return the SHOWLABEL for GetLegendGraphic requests
    """
    try:
        if 'colorbaronly' in request.GET and request.GET['colorbaronly'].lower() == 'true':
            return False
        else:
            return request.GET['showlabel'].lower() == 'true'
    except KeyError:
        return True


def get_units(request, units):
    """
    Return the UNITS for GetLegendGraphic requests
    """
    try:
        return request.GET['unitlabel'].lower()
    except KeyError:
        return units


def get_logscale(request, default_logscale):
    """
    Return the LOGSCALE for GetLegendGraphic requests
    """
    try:
        return request.GET['logscale'].lower() == 'true'
    except KeyError:
        return default_logscale


def get_horizontal(request):
    """
    Return the horizontal for GetLegendGraphic requests
    """
    try:
        return request.GET['horizontal'].lower() == 'true'
    except KeyError:
        return False


def get_show_values(request):
    """
    Return the SHOWVALUES for GetLegendGraphic requests
    """
    try:
        if 'colorbaronly' in request.GET and request.GET['colorbaronly'].lower() == 'true':
            return False
        else:
            return request.GET['showvalues'].lower() == 'true'
    except KeyError:
        return True


def get_num_contours(request, default=None):
    """
    Return the NUMCONTOURS for GetLegendGraphic requests
    """
    default = default or 8
    try:
        return int(float(request.GET['numcontours'].lower()))
    except (KeyError, ValueError):
        return default


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
    projstr = request.GET.get("srs", request.GET.get("crs"))
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
        dt = parse(time)
        if dt.tzinfo is not None:
            utc_dt = dt.astimezone(tzutc())  # convert UTC if tzinfo is available
            utc_tz_naive = utc_dt.replace(tzinfo=None)
        else:
            utc_tz_naive = dt
        return utc_tz_naive


def get_times(request):
    """
    Return the min and max times
    """
    time = request.GET.get('time')
    if not time:
        time = date.today().isoformat() + "T00:00:00"
    times = sorted([ parse(t) for t in time.split("/") ])
    # Convert tz-aware datetimes to native datetimes
    times = [ tz_aware_to_native(t) for t in times ]
    return DotDict(min=times[0], max=times[-1])


def get_colormap(request, parameter=None, default=None):
    parameter = parameter or 'styles'
    default = default or 'cubehelix'
    try:
        from matplotlib.pyplot import colormaps
        requested_cm = split(request.GET.get(parameter).split(',')[0], '_', maxsplit=1)[1]
        assert requested_cm
        return next(x for x in colormaps() if x.lower() == requested_cm.lower())
    except (AssertionError, IndexError, AttributeError, TypeError, StopIteration):
        return default


def get_imagetype(request, parameter=None, default=None):
    parameter = parameter or 'styles'
    default = default or 'filledcontours'
    try:
        z = split(request.GET.get(parameter).split(',')[0], '_', maxsplit=1)[0].lower()
        assert z
        return z
    except (AssertionError, IndexError, AttributeError, TypeError):
        return default


def get_vectorscale(request):
    try:
        vectorscale = float(request.GET.get('vectorscale'))
    except (AttributeError, TypeError):
        vectorscale = 1
    return vectorscale


def get_vectorstep(request):
    try:
        vectorstep = int(request.GET.get('vectorstep'))
    except TypeError:
        vectorstep = 1  # equivalent to getting all the data
    return vectorstep


def get_colorscalerange(request, default_min, default_max):
    try:
        climits = sorted([ float(x) for x in request.GET.get('colorscalerange').split(',') ])
        return DotDict(min=climits[0], max=climits[-1])
    except (AttributeError, TypeError):
        return DotDict(min=default_min, max=default_max)


def get_dimensions(request, default_width=None, default_height=None):
    """
    Return width and height of requested view.
    RETURNS width, height request should be in pixel units.
    """
    try:
        width = float(request.GET.get("width"))
        height = float(request.GET.get("height"))
        return DotDict(width=width, height=height)
    except BaseException:
        return DotDict(width=default_width, height=default_height)


def get_gfi_positions(xy, bbox, crs, dims):
    """ Returns the latitude and longitude the GFI should be performed at"""
    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    lon, lat = pyproj.transform(
        crs,
        EPSG4326,
        bbox.minx + ((bbox.maxx - bbox.minx) * (xy.x / dims.width)),
        bbox.maxy - ((bbox.maxy - bbox.miny) * (xy.y / dims.height))
    )
    return DotDict(latitude=lat, longitude=lon)


def get_item(request):
    """
    Returns the GetMetadata 'item' function
    """
    try:
        return request.GET["item"].lower()
    except KeyError:
        return None
