# -*- coding: utf-8 -*-
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


def lat_lon_subset_idx(lon, lat, lonmin, latmin, lonmax, latmax, padding=0.18):
    """
    A function to return the indicies of lat, lon within a bounding box.
    Padding is leftover from old sciwms code, I believe it was to include triangles
    lying just outside the region of interest so that there are no holes in the
    rendered image.
    """
    if lonmin > lonmax:
        lonmin = lonmin * -1.0  # TODO: this should solve USW integration sites at wide zoom, but is it best way?
    return np.asarray(np.where(
        (lat <= (latmax + padding)) & (lat >= (latmin - padding)) &
        (lon <= (lonmax + padding)) & (lon >= (lonmin - padding)),)).squeeze()


def faces_subset_idx(face_indicies, spatial_idx):
    """
    Return row indicies into the nv data structure which have indicies
    inside the bounding box defined by lat_lon_subset_idx
    """
    return np.asarray(np.where(np.all(np.in1d(face_indicies, spatial_idx).reshape(face_indicies.shape), 1))).squeeze()


def blank_canvas(width, height, dpi=5):
    """
    return a transparent (blank) response
    used for tiles with no intersection with the current view or for some other error.
    """
    fig = Figure(dpi=dpi, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    fig.set_figheight(height/dpi)
    fig.set_figwidth(width/dpi)
    ax.set_frame_on(False)
    ax.set_clip_on(False)
    ax.set_position([0, 0, 1, 1])
    canvas = FigureCanvasAgg(fig)
    return canvas
