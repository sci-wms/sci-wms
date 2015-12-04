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
    return np.asarray(np.where(np.all(np.in1d(face_indicies, spatial_idx).reshape(face_indicies.shape), axis=1))).squeeze()


def face_idx_from_node_idx(faces, spatial_idx):
    subset_indexes = np.where(spatial_idx==True)  # Convert from bool array to index array  noqa
    intersect = np.in1d(faces, subset_indexes).reshape(faces.shape)  # Intersect on the node indexes
    faces_idx = np.all(intersect, axis=1)  # Only save faces where there are all nodes indexed
    return faces_idx


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


def ugrid_lat_lon_subset_idx(lon, lat, bbox, padding=None):
    """
    Assumes the size of lat/lon are equal (UGRID variables).
    Returns a boolean mask array of the indexes, suitable for slicing
    """

    padding = padding or 0.18

    minlon = bbox[0] - padding
    minlat = bbox[1] - padding
    maxlon = bbox[2] + padding
    maxlat = bbox[3] + padding

    land = np.logical_and
    return land(land(lon >= minlon, lon <= maxlon),
                land(lat >= minlat, lat <= maxlat))
