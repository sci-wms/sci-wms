#ugrid
import os, sys
import numpy as np
from matplotlib.pylab import get_cmap
import pywms.server_local_config as config
from matplotlib.collections import PolyCollection
import matplotlib.tri as Tri
import matplotlib.path as mpath

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
            #var1[np.isnan(var2)] = np.nan # shouldnt be necessary in ...
            #var2[np.isnan(var1)] = np.nan
            var1 = var1 + var2
            var2 = None
    return var1, var2

def plot(lon, lat, lonn, latn, nv, var1, var2, actions, m, ax, fig, **kwargs):
    patch1 = None
    aspect = kwargs.get('aspect', None)
    height = kwargs.get('height')
    width = kwargs.get('width')
    norm = kwargs.get('norm')
    cmap = get_cmap(kwargs.get('cmap', 'jet'))
    cmin = kwargs.get('cmin', "None")
    cmax = kwargs.get('cmax', "None")
    magnitude = kwargs.get('magnitude', "False")
    topology_type = kwargs.get('topology_type', 'node')
    fig.set_figheight(height/80.0)
    fig.set_figwidth(width/80.0)
    if var1 is not None:
        if var2 is not None:
            mag = np.sqrt(var1**2 + var2**2)
        else:
            if magnitude == "True":
                mag = np.abs(var1)
            else:
                mag = var1
        mag = mag.squeeze()
        if "facets" in actions:
            facet(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, kwargs)
        elif "vectors" in actions:
            vectors(lon, lat, lonn, latn, var1, var2, mag, m, ax, norm, cmap, magnitude, topology_type)
        elif "barbs" in actions:
            barbs(lon, lat, lonn, latn, var1, var2, mag, m, ax, norm, cmin, cmax, cmap, magnitude, topology_type)
        else:
            lonmin = kwargs.get("lonmin")
            latmin = kwargs.get("latmin")
            lonmax = kwargs.get("lonmax")
            latmax = kwargs.get("latmax")
            dataset = kwargs.get("dataset")
            continuous = kwargs.get("continuous")
            projection = kwargs.get("projection")
            if "pcolor" in actions:
                fig, m = pcolor(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmap, topology_type, fig, height, width, lonmin, latmin, lonmax, latmax, dataset, continuous, projection)
            elif "filledcontours" in actions:
                fig, m = fcontour(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, fig, height, width, lonmin, latmin, lonmax, latmax, dataset, continuous, projection)
            elif "contours" in actions:
                fig, m = contour(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, fig, height, width, lonmin, latmin, lonmax, latmax, dataset, continuous, projection)
    return fig, m

def pcolor(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmap, topology_type, fig, height, width, lonmin, latmin, lonmax, latmax, dataset, continuous, projection):
    from matplotlib.mlab import griddata
    if topology_type.lower() == "cell":
        lon, lat = m(lon, lat)
        lonn, latn = m(lonn, latn)
    else:
        lon, lat = m(lonn, latn)
        lonn, latn = lon, lat
    num = int( (lonmax - lonmin) *  320 )
    xi = np.arange(m.xmin, m.xmax, num)
    yi = np.arange(m.ymin, m.ymax, num)
    if topology_type.lower() == "node":
        n = np.unique(nv)
        zi = griddata(lon[n], lat[n], mag[n], xi, yi, interp='nn')
    else:
        zi = griddata(lon, lat, mag, xi, yi, interp='nn')
    fig, m, patch1 = cookie_cutter(dataset, fig, m, lonmin, latmin, lonmax, latmax, projection, continuous)
    m.imshow(zi, norm=norm, cmap=cmap, clip_path=patch1, interpolation="nearest")
    return fig, m

def contour(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, fig, height, width, lonmin, latmin, lonmax, latmax, dataset, continuous, projection):
    if (cmin == "None") or (cmax == "None"):
        levs = None
    else:
        levs = np.arange(0, 12)*(cmax-cmin)/10
    if topology_type.lower() == 'cell':
        lon, lat = m(lon, lat)
        trid = Tri.Triangulation(lon, lat)
        m.ax.tricontour(trid, mag, norm=norm, levels=levs, antialiased=True, linewidth=2, cmap=get_cmap(cmap))
        fig, m, patch1 = cookie_cutter(dataset, fig, m, lonmin, latmin, lonmax, latmax, projection, continuous)
    else:
        lonn, latn = m(lonn, latn)
        tri = Tri.Triangulation(lonn, latn, triangles=nv)
        m.ax.tricontour(tri, mag, norm=norm, levels=levs, antialiased=True, linewidth=2, cmap=get_cmap(cmap))
    return fig, m

def fcontour(lon, lat, lonn, latn, mag, nv, m, ax, norm, cmin, cmax, cmap, topology_type, fig, height, width, lonmin, latmin, lonmax, latmax, dataset, continuous, projection):
    if (cmin == "None") or (cmax == "None"):
        levs = None
    else:
        levs = np.arange(1, 12)*(cmax-cmin)/10
        levs = np.hstack(([-99999], levs, [99999]))
    if topology_type.lower() == 'cell':
        lon, lat = m(lon, lat)
        trid = Tri.Triangulation(lon, lat)
        m.ax.tricontourf(trid, mag, norm=norm, levels=levs, antialiased=False, linewidth=0, cmap=get_cmap(cmap))
        fig, m, patch1 = cookie_cutter(dataset, fig, m, lonmin, latmin, lonmax, latmax, projection, continuous)
    else:
        lonn, latn = m(lonn, latn)
        tri = Tri.Triangulation(lonn, latn, triangles=nv)
        m.ax.tricontourf(tri, mag, norm=norm, levels=levs, antialiased=False, linewidth=0, cmap=get_cmap(cmap))
    return fig, m

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
            length=4.5,
            pivot='middle',
            barb_increments=dict(half=full/2., full=full, flag=flag),
            #units='xy',
            cmap=cmap,
            norm=norm,
            #clim=climits,
            linewidth=1.2,
            sizes=dict(emptybarb=0.2, spacing=0.14, height=0.5),
            #antialiased=True,
            )
    else:
        m.ax.barbs(lon, lat, var1, var2, mag,
            length=4.5,
            pivot='middle',
            barb_increments=dict(half=full/2., full=full, flag=flag),
            #units='xy',
            cmap=cmap,
            norm=norm,
            #clim=climits,
            linewidth=1.2,
            sizes=dict(emptybarb=0.2, spacing=.14, height=0.5),
            #antialiased=True,
            )

# Utility functions to aid in pcolor, and contouring styles
def correct_continuous(x, continuous, lonmin, latmin, lonmax, latmax):
    if continuous is True:
        if lonmin < 0:
            x[np.where(x > 0)] = x[np.where(x > 0)] - 360
            x[np.where(x < lonmax-359)] = x[np.where(x < lonmax-359)] + 360
        else:
            x[np.where(x < lonmax-359)] = x[np.where(x < lonmax-359)] + 360
    return x

def create_path_codes(x):
    allcodes = np.ones(len(x),dtype=mpath.Path.code_type) * mpath.Path.LINETO
    allcodes[0] = mpath.Path.MOVETO
    allcodes[-1] = mpath.Path.CLOSEPOLY
    return allcodes

def add_path_codes(holex, allcodes):
    newcodes  = np.ones(len(holex), dtype=mpath.Path.code_type) * mpath.Path.LINETO
    newcodes[0] = mpath.Path.MOVETO
    newcodes[-1] = mpath.Path.CLOSEPOLY
    allcodes = np.concatenate((allcodes, newcodes))
    return allcodes

def get_domain_as_patch(dataset, m, lonmin, latmin, lonmax, latmax, continuous):
    import shapely.geometry
    try:
        import cPickle as pickle
    except ImportError:
        import Pickle as pickle
    # Open domain
    f = open(os.path.join(config.topologypath, dataset + '.domain'))
    domain = pickle.load(f)
    f.close()
    # convert extent bbox to Shapely Polygon object
    if continuous is True:
        if lonmin < 0:
            box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 0, latmax),
                                                 shapely.geometry.box(0, latmin, lonmax, latmax)))
        else:
            box = shapely.geometry.MultiPolygon((shapely.geometry.box(lonmin, latmin, 180, latmax),
                                                 shapely.geometry.box(-180, latmin, lonmax-360, latmax)))
    else:
        box = shapely.geometry.box(lonmin, latmin, lonmax, latmax)
    # Find the intersection of the dataset domain and view extent
    domain = domain.intersection(box)
    # Create a path out of the polygon for clipping
    if domain.geom_type == "Polygon":
        x, y = domain.exterior.xy
        x = np.asarray(x)
        # Correct continous
        x = correct_continuous(x, continuous, lonmin, latmin, lonmax, latmax)
        x, y = m(x, y)
        x = np.hstack((np.asarray(x),x[0]))
        y = np.hstack((np.asarray(y),y[0]))
        allcodes = create_path_codes(x)
        for hole in domain.interiors:
            holex, holey = hole.xy
            holex = np.asarray(holex)
            # Correct continous
            holex = correct_continuous(holex, continuous, lonmin, latmin, lonmax, latmax)
            holex, holey = m(holex, holey)
            allcodes = add_path_codes(holex, allcodes)
            x = np.concatenate((x, holex))
            y = np.concatenate((y, holey))
        p = mpath.Path(np.asarray((x,y)).T, codes = allcodes)
    elif domain.geom_type == "MultiPolygon":
        for i, part in enumerate(domain.geoms):
            x, y = part.exterior.xy
            x = np.asarray(x)
            # Correct continous
            x = correct_continuous(x, continuous, lonmin, latmin, lonmax, latmax)
            x, y = m(x, y)
            x = np.hstack((np.asarray(x),x[0]))
            y = np.hstack((np.asarray(y),y[0]))
            allcodes = create_path_codes(x)
            try:
                for hole in part.interiors:
                    holex, holey = hole.xy
                    holex = np.asarray(holex)
                    # Correct continous
                    holex = correct_continuous(holex, continuous, lonmin, latmin, lonmax, latmax)
                    holex, holey = m(holex, holey)
                    allcodes = add_path_codes(holex, allcodes)
                    x = np.concatenate((x, holex))
                    y = np.concatenate((y, holey))
            except:
                pass
            p = mpath.Path(np.asarray((x,y)).T, codes = allcodes)
    return p

def prepare_axes(m, lonmin, latmin, lonmax, latmax):
    lonmax1, latmax1 = m(lonmax, latmax)
    lonmin1, latmin1 = m(lonmin, latmin)
    m.ax.set_xlim(lonmin1, lonmax1)
    m.ax.set_ylim(latmin1, latmax1)
    m.ax.set_frame_on(False)
    m.ax.set_clip_on(False)
    m.ax.set_position([0,0,1,1])

def create_projected_fig(lonmin, latmin, lonmax, latmax, projection, height, width):
    from mpl_toolkits.basemap import Basemap
    from matplotlib.figure import Figure
    fig = Figure(dpi=80, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    fig.set_figheight(height)
    fig.set_figwidth(width)
    m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin,
            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
            resolution=None,
            lat_ts = 0.0,
            suppress_ticks=True)
    m.ax = fig.add_axes([0, 0, 1, 1], xticks=[], yticks=[])
    return fig, m

def figure2array(fig):
    from StringIO import StringIO
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.image import imread as mread
    buf = StringIO()
    canvas = FigureCanvasAgg(fig)
    canvas.print_png(buf)
    buf.seek(0)
    im = mread(buf)
    buf.close()
    del fig
    return im

def cookie_cutter(dataset, fig, m, lonmin, latmin, lonmax, latmax, projection, cont):
    import matplotlib.patches as mpatches

    # Convert current unclipped figure to an image array
    height, width = fig.get_figheight(), fig.get_figwidth()
    prepare_axes(m, lonmin, latmin, lonmax, latmax)
    im = figure2array(fig)

    # New figure and m created here
    fig, m = create_projected_fig(lonmin, latmin, lonmax, latmax, projection, height, width)

    # Get the current extent of the dataset domain as path
    p = get_domain_as_patch(dataset, m, lonmin, latmin, lonmax, latmax, cont)
    patch1 = mpatches.PathPatch(p, facecolor='none', edgecolor='none')

    # Clip the image to the dataset's domain
    m.ax.add_patch(patch1)
    fig.figimage(im, clip_path=patch1)
    patch1.set_color('none')
    return fig, m, patch1 # Return a new fig instance