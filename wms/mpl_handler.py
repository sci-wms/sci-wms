# -*- coding: utf-8 -*-
from django.http import HttpResponse

import pyproj
import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from wms import logger


def _get_common_params(request):
    bbox = request.GET['bbox']
    width = request.GET['width']
    height = request.GET['height']
    colormap = request.GET['colormap']
    colorscalerange = request.GET['colorscalerange']
    cmin = colorscalerange.min
    cmax = colorscalerange.max
    crs = request.GET['crs']
    params = (bbox, width,
              height, colormap,
              cmin, cmax, crs
              )
    return params


def tricontourf_response(tri_subset,
                         data,
                         request,
                         dpi=80.0,
                         nlvls=15):
    """
    triang_subset is a matplotlib.Tri object in lat/lon units (will be converted to projected coordinates)
    xmin, ymin, xmax, ymax is the bounding pox of the plot in PROJETED COORDINATES!!!
    request is the original getMap request object
    """
    bbox = request.GET['bbox']
    width = request.GET['width']
    height = request.GET['height']
    colormap = request.GET['colormap']
    colorscalerange = request.GET['colorscalerange']
    cmin = colorscalerange.min
    cmax = colorscalerange.max
    crs = request.GET['crs']

    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    tri_subset.x, tri_subset.y = pyproj.transform(EPSG4326, crs, tri_subset.x, tri_subset.y)

    fig = Figure(dpi=dpi, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figheight(height/dpi)
    fig.set_figwidth(width/dpi)

    ax = fig.add_axes([0., 0., 1., 1.], xticks=[], yticks=[])
    ax.set_axis_off()

    # Set out of bound data to NaN so it shows transparent?
    # Set to black like ncWMS?
    # Configurable by user?
    if cmin and cmax:
        data[data > cmax] = cmax
        data[data < cmin] = cmin
        lvls = np.linspace(float(cmin), float(cmax), int(nlvls))
        ax.tricontourf(tri_subset, data, levels=lvls, cmap=colormap)
    else:
        ax.tricontourf(tri_subset, data, cmap=colormap)

    ax.set_xlim(bbox.minx, bbox.maxx)
    ax.set_ylim(bbox.miny, bbox.maxy)
    ax.set_frame_on(False)
    ax.set_clip_on(False)
    ax.set_position([0., 0., 1., 1.])

    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def quiver_response(lon,
                    lat,
                    dx,
                    dy,
                    request,
                    unit_vectors=False,
                    dpi=80):

    bbox = request.GET['bbox']
    width = request.GET['width']
    height = request.GET['height']
    colormap = request.GET['colormap']
    colorscalerange = request.GET['colorscalerange']
    cmin = colorscalerange.min
    cmax = colorscalerange.max
    crs = request.GET['crs']

    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    x, y = pyproj.transform(EPSG4326, crs, lon, lat)  # TODO order for non-inverse?

    fig = Figure(dpi=dpi, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figheight(height/dpi)
    fig.set_figwidth(width/dpi)

    ax = fig.add_axes([0., 0., 1., 1.], xticks=[], yticks=[])
    ax.set_axis_off()
    mags = np.sqrt(dx**2 + dy**2)

    cmap = mpl.cm.get_cmap(colormap)
    # Set out of bound data to NaN so it shows transparent?
    # Set to black like ncWMS?
    # Configurable by user?
    norm = None
    if cmin is not None and cmax is not None:
        mags[mags > cmax] = cmax
        mags[mags < cmin] = cmin
        bounds = np.linspace(cmin, cmax, 15)
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    # plot unit vectors
    if unit_vectors:
        ax.quiver(x, y, dx/mags, dy/mags, mags, cmap=cmap)
    else:
        ax.quiver(x, y, dx, dy, mags, cmap=cmap, norm=norm)

    ax.set_xlim(bbox.minx, bbox.maxx)
    ax.set_ylim(bbox.miny, bbox.maxy)
    ax.set_frame_on(False)
    ax.set_clip_on(False)
    ax.set_position([0., 0., 1., 1.])

    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def contourf_response(lon,
                      lat,
                      data,
                      request,
                      dpi=80
                      ):
    params = _get_common_params(request)
    bbox, width, height, colormap, cmin, cmax, crs = params
    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    x, y = pyproj.transform(EPSG4326, crs, lon, lat)
    fig = Figure(dpi=dpi, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figheight(height/dpi)
    fig.set_figwidth(width/dpi)
    ax = fig.add_axes([0., 0., 1., 1.], xticks=[], yticks=[])
    ax.set_axis_off()
    cmap = mpl.cm.get_cmap(colormap)
    
    if cmin and cmax:
        data[data > cmax] = cmax
        data[data < cmin] = cmin
        bounds = np.linspace(cmin, cmax, 15)
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        bounds = np.linspace(cmin, cmax, 15)
    else:
        norm = None
    ax.contourf(x, y, data, vmin=5, vmax=30, norm=norm) 
    ax.set_xlim(bbox.minx, bbox.maxx)
    ax.set_ylim(bbox.miny, bbox.maxy)
    ax.set_frame_on(False)
    ax.set_clip_on(False)
    ax.set_position([0., 0., 1., 1.])
    
    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response   


def pcolormesh_response(lon,
                        lat,
                        data,
                        request,
                        dpi=80):
    params = _get_common_params(request)
    bbox, width, height, colormap, cmin, cmax, crs = params
    
    EPSG4326 = pyproj.Proj(init='EPSG:4326')
    x, y = pyproj.transform(EPSG4326, crs, lon, lat)
    fig = Figure(dpi=dpi, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figheight(height/dpi)
    fig.set_figwidth(width/dpi)
    ax = fig.add_axes([0., 0., 1., 1.], xticks=[], yticks=[])
    ax.set_axis_off()
    cmap = mpl.cm.get_cmap(colormap)
    
    if cmin and cmax:
        data[data > cmax] = cmax
        data[data < cmin] = cmin
        bounds = np.linspace(cmin, cmax, 15)
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
        bounds = np.linspace(cmin, cmax, 15)
    else:
        norm = None
    masked = np.ma.masked_invalid(data)
    ax.pcolormesh(x, y, masked, vmin=5, vmax=30, norm=norm) 
    ax.set_xlim(bbox.minx, bbox.maxx)
    ax.set_ylim(bbox.miny, bbox.maxy)
    ax.set_frame_on(False)
    ax.set_clip_on(False)
    ax.set_position([0., 0., 1., 1.])
    
    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response   
        