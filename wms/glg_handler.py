# -*- coding: utf-8 -*-
from django.http import HttpResponse

import numpy as np

import matplotlib

from matplotlib.pyplot import get_cmap, colorbar, legend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

from wms import logger

from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Bitstream Vera Sans']
rcParams['font.serif'] = ['Bitstream Vera Sans']
rcParams['font.size'] = '10'
rcParams['figure.autolayout'] = True
rcParams['savefig.dpi'] = 72.


def create_axis(request, position=None):
    position = position or [0, 0, 1, 1]
    # Create figure
    plt.close('all')
    dpi = 72.
    width = int(request.GET['width'])
    height = int(request.GET['height'])
    fig = plt.figure(dpi=dpi, figsize=(width / dpi, height / dpi), facecolor=None, edgecolor=None, frameon=False, tight_layout=True)
    fig.set_alpha(0)
    ax = fig.add_axes(position)

    csr = request.GET['colorscalerange']
    if request.GET['logscale'] is True:
        norm = matplotlib.colors.LogNorm(vmin=csr.min, vmax=csr.max, clip=False)
    else:
        norm = matplotlib.colors.Normalize(vmin=csr.min, vmax=csr.max, clip=False)

    return fig, ax, norm


def figure_response(fig, request, adjust=None, **kwargs):

    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response, bbox_inches='tight', pad_inches=0.1, **kwargs)
    return response


def get_position(request):
    if request.GET['horizontal'] is True:
        base = [0.08, 0.5, 0.8, 0.4]
        if request.GET['showlabel'] is False:
            base[3] += 0.1
        if request.GET['showvalues'] is False:
            base[3] += 0.2
    else:
        base = [0.05, 0.1, 0.4, 0.8]
        if request.GET['showlabel'] is False:
            base[2] += 0.1
        if request.GET['showvalues'] is False:
            base[2] += 0.2

    return base


def filledcontour(request):
    # Create figure
    fig, ax, norm = create_axis(request, get_position(request))

    orientation = 'vertical'
    if request.GET['horizontal'] is True:
        orientation = 'horizontal'
    csr = request.GET['colorscalerange']

    if request.GET['logscale'] is True:
        levs = np.hstack(([csr.min-3], np.linspace(csr.min, csr.max, request.GET['numcontours']), [csr.max+40]))
        x, y = np.meshgrid(np.arange(1), np.arange(1))
        cs = ax.contourf(x, y, x, levels=levs, norm=norm, cmap=get_cmap(request.GET['colormap']))
        cb = colorbar(mappable=cs, cax=ax, orientation=orientation, spacing='proportional', extendrect=False, use_gridspec=True)
        if request.GET['showvalues'] is False:
            cb.set_ticks([])
        else:
            cb.set_ticks(levs[1:-1])
            cb.set_ticklabels([ "%.1f" % x for x in levs[1:-1] ])

    else:
        levs = np.linspace(csr.min, csr.max, request.GET['numcontours'])
        x, y = np.meshgrid(np.arange(1), np.arange(1))
        cs = ax.contourf(x, y, x, levels=levs, norm=norm, cmap=get_cmap(request.GET['colormap']), extend='both')
        cb = colorbar(mappable=cs, cax=ax, orientation=orientation, spacing='proportional', extendrect=False, use_gridspec=True)
        if request.GET['showvalues'] is False:
            cb.set_ticks([])
        else:
            cb.set_ticks(levs)
            cb.set_ticklabels([ "%.1f" % x for x in levs ])

    if request.GET['showlabel'] is True:
        cb.set_label(request.GET['units'])

    # Return HttpResponse
    return figure_response(fig, request)


def contour(request):

    # Create figure
    fig, ax, norm = create_axis(request)
    ax.set_axis_off()

    csr = request.GET['colorscalerange']

    if request.GET['logscale'] is True:
        levs = np.hstack(([csr.min-1], np.linspace(csr.min, csr.max, request.GET['numcontours']), [csr.max+1]))
        levs_labels = [ "%.1f" % x for x in levs[1:-1] ]
        if request.GET['showvalues'] is False:
            levs_labels = [ '' for x in range(levs.size-2) ]
        x, y = np.meshgrid(np.arange(1), np.arange(1))
        cs = ax.contourf(x, y, x, levels=levs, norm=norm, cmap=get_cmap(request.GET['colormap']))
        proxy = [plt.Rectangle((0, 0), 0, 0, fc=pc.get_facecolor()[0]) for pc in cs.collections]

    else:
        levs = np.linspace(csr.min, csr.max, request.GET['numcontours'])
        levs_labels = [ "%.1f" % x for x in levs ]
        if request.GET['showvalues'] is False:
            levs_labels = [ '' for x in range(levs.size) ]
        x, y = np.meshgrid(np.arange(1), np.arange(1))
        cs = ax.contourf(x, y, x, levels=levs, norm=norm, cmap=get_cmap(request.GET['colormap']), extend='max')
        proxy = [plt.Rectangle((0, 0), 0, 0, fc=pc.get_facecolor()[0]) for pc in cs.collections]

    params = dict()
    if request.GET['horizontal'] is True:
        columns = 5
        if request.GET['numcontours'] > 20:
            columns = request.GET['numcontours'] / 10
        params = dict(labelspacing=0, mode="expand", ncol=columns)

    cb = legend(proxy, levs_labels, loc=10, borderaxespad=0., frameon=False, **params)

    if request.GET['showlabel'] is True:
        cb.set_title(request.GET['units'])

    # Return HttpResponse
    return figure_response(fig, request, bbox_extra_artists=(cb,))


def vector(request):
    raise NotImplementedError


def barb(request):
    raise NotImplementedError


def gradiant(request):
    # Create figure
    fig, ax, norm = create_axis(request, get_position(request))

    orientation = 'vertical'
    if request.GET['horizontal'] is True:
        orientation = 'horizontal'
    cb = matplotlib.colorbar.ColorbarBase(ax, cmap=get_cmap(request.GET['colormap']), norm=norm, orientation=orientation)

    if request.GET['showvalues'] is False:
        cb.set_ticks([])
    else:
        csr = request.GET['colorscalerange']
        ticks = np.linspace(csr.min, csr.max, 5)
        cb.set_ticks(ticks)
        cb.set_ticklabels([ "%.1f" % x for x in ticks ])

    if request.GET['showlabel'] is True:
        cb.set_label(request.GET['units'])

    # Return HttpResponse
    return figure_response(fig, request)
