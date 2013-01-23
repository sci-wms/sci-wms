#ugrid
import os, sys
import numpy as np
from matplotlib.pylab import get_cmap
#import matplotlib
#from collections import deque
#from StringIO import StringIO
#from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PolyCollection
#from matplotlib.backends.backend_agg import FigureCanvasAgg
#from mpl_toolkits.basemap import pyproj
#from matplotlib.figure import Figure
import matplotlib.tri as Tri

#try:
#    import cPickle as pickle
#except ImportError:
#    import Pickle as pickle

def subset(latmin, lonmin, latmax, lonmax, lat, lon):
    index = np.asarray(np.where(
        (lat <= latmax+.18) & (lat >= latmin-.18) &
        (lon <= lonmax+.18) & (lon >= lonmin-.18),)).squeeze()
    lat = lat[index]
    lon = lon[index]
    if not len(index) > 0:
        index = None
    return index, lat, lon

def get_nodes(topology):
    latn = topology.variables['lat'][:]
    lonn = topology.variables['lon'][:]
    return latn, lonn

def get_topologyarray(topology, index):
    nvtemp = topology.variables['nv'][:,:]
    nv = nvtemp[:,index].T-1 # Convert to 0 based indexing TODO:convert in the topology generation
    return nv

def varfromnc(nc, t, layer, var):
    if len(nc.variables[var].shape) == 3:
        return nc.variables[var][t, layer[0], :]
    elif len(nc.variables[var].shape) == 2:
        return nc.variables[var][t, :]
    elif len(nc.variables[var].shape) == 1:
        return nc.variables[var][:]

def getvar(datasetnc, t, layer, variables, index):
    special_function = ""
    if index is None:
        var1 = None
        var2 = None
    else:
        if "+" in variables[0]:
            variables = variables[0].split("+")
            special_function = "+"
        var1 = varfromnc(datasetnc , t, layer, variables[0])
        if len(variables) > 1:
            var2 = varfromnc(datasetnc, t, layer, variables[1])
        if len(var1.shape) > 2:
            var1 = var1[:, :, index]
            try:
                var2 = var2[:, :, index]
            except:
                var2 = None
        elif len(var1.shape) > 1:
            var1 = var1[:, index]
            try:
                var2 = var2[:, index]
            except:
                var2 = None
        else:
            var1, var2 = None, None
        if special_function == "+":
            var1 = var1 + var2
            var2 = None
    return var1, var2

def plot(lon, lat, lonn, latn, nv, var1, var2, actions, m, ax, fig, **kwargs):
    aspect = kwargs.get('aspect', None)
    height = kwargs.get('height')
    width = kwargs.get('width')
    norm = kwargs.get('norm')
    cmap = get_cmap(kwargs.get('cmap', 'jet'))
    cmin = kwargs.get('cmin', "None")
    cmax = kwargs.get('cmax', "None")
    magnitude = kwargs.get('magnitude', 2)
    topology_type = kwargs.get('topology_type', 'node')
    if var1 is not None:
        if var2 is not None:
            mag = np.sqrt(var1**2 + var2**2)
        else:
            mag = var1
        mag = mag.squeeze()
        if "pcolor" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            pcolor(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmap, topology_type, kwargs)
        if "facets" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            facet(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, kwargs)
        elif "filledcontours" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            fcontour(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmap, topology_type, kwargs)
        elif "contours" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            contour(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmap, topology_type, fig, height, width, kwargs)
        elif "vectors" in actions:
            #fig.set_figheight(height/80.0/aspect)
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            vectors(lon, lat, lonn, latn, var1, var2, mag, m, ax, norm, cmap, magnitude, topology_type)
        elif "barbs" in actions:
            #fig.set_figheight(height/80.0/aspect)
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            barbs(lon, lat, lonn, latn, var1, var2, mag, m, ax, norm, cmin, cmax, cmap, magnitude, topology_type)

def facet(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, kwargs):
    lonn, latn = m(lonn, latn)
    tri = Tri.Triangulation(lonn,latn,triangles=nv)
    if topology_type.lower() == 'cell':
        verts = np.concatenate((tri.x[tri.triangles][...,np.newaxis],\
                                tri.y[tri.triangles][...,np.newaxis]), axis=2)
        collection = PolyCollection(verts,
                                    cmap=cmap,
                                    norm=norm,
                                    )
        collection.set_array(mag)
        collection.set_edgecolor('none')
        m.ax.add_collection(collection)
    else:
        m.ax.tripcolor(tri, mag,
                       shading="",
                       norm=norm,
                       cmap=cmap,
                       )

def vectors(lon, lat, lonn, latn, var1, var2, mag, m, ax, norm, cmap, magnitude, topology_type):
    if magnitude == "True":
        arrowsize = None
    elif magnitude == "False":
        arrowsize = 2.
    elif magnitude == "None":
        arrowsize = None
    else:
        arrowsize = float(magnitude)
    if topology_type.lower() == 'cell':
        pass
    else:
        lon, lat = lonn, latn
    lon, lat = m(lon, lat)
    if topology_type.lower() == 'node':
        n = np.unique(nv)
        m.quiver(lon[n], lat[n], var1[n], var2[n], mag[n],
            pivot='mid',
            units='xy', #xy
            cmap=cmap,
            norm=norm,
            minlength=.5,
            scale=arrowsize,
            scale_units='inches',
            )
    else:
        m.quiver(lon, lat, var1, var2, mag,
            pivot='mid',
            units='xy', #xy
            cmap=cmap,
            norm=norm,
            minlength=.5,
            scale=arrowsize,
            scale_units='inches',
            )

def barbs(lon, lat, lonn, latn, var1, var2, mag, m, ax, norm, cmin, cmax, cmap, magnitude, topology_type):
    if magnitude == "True":
        arrowsize = None
    elif magnitude == "False":
        arrowsize = 2.
    elif magnitude == "None":
        arrowsize = None
    else:
        arrowsize = float(magnitude)
    if (cmin == "None") or (cmax == "None"):
        full = 10.#.2
        flag = 50.#1.
    else:
        full = cmin
        flag = cmax
    if topology_type.lower() == 'cell':
        pass
    else:
        lon, lat = lonn, latn
    lon, lat = m(lon, lat)
    if topology_type.lower() == 'node':
        n = np.unique(nv)
        m.ax.barbs(lon[n], lat[n], var1[n], var2[n], mag[n],
            length=7.,
            pivot='middle',
            barb_increments=dict(half=full/2., full=full, flag=flag),
            #units='xy',
            cmap=cmap,
            norm=norm,
            #clim=climits,
            linewidth=1.7,
            sizes=dict(emptybarb=0.2, spacing=0.14, height=0.5),
            #antialiased=True,
            )
    else:
        m.ax.barbs(lon, lat, var1, var2, mag,
            length=7.,
            pivot='middle',
            barb_increments=dict(half=full/2., full=full, flag=flag),
            #units='xy',
            cmap=cmap,
            norm=norm,
            #clim=climits,
            linewidth=1.7,
            sizes=dict(emptybarb=0.2, spacing=.14, height=0.5),
            #antialiased=True,
            )
