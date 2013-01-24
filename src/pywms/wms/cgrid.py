#cgrid
import os, sys
import numpy as np
from matplotlib.pylab import get_cmap

def subset(latmin, lonmin, latmax, lonmax, lat, lon):
    index = np.asarray(np.where(
        (lat <= latmax+.18) & (lat >= latmin-.18) &
        (lon <= lonmax+.18) & (lon >= lonmin-.18),)).squeeze()
    if index.shape[1] > 0:
        ind = np.asarray(range(np.min(np.min(index[0])),np.max(np.max(index[0]))+1))
        jnd = np.asarray(range(np.min(np.min(index[1])),np.max(np.max(index[1]))+1))
        lat = lat[ind[0]:ind[-1], jnd[0]:jnd[-1]]
        lon = lon[ind[0]:ind[-1], jnd[0]:jnd[-1]]
    else:
        index = None
        lat = np.asarray([[],[]])
        lon = np.asarray([[],[]])
    return index, lat, lon

def getvar(datasetnc, t, layer, variables, index):
    special_function = ""
    if index is None:
        var1 = None
        var2 = None
    else:
        if "+" in variables[0]:
            variables = variables[0].split("+")
            special_function = "+"
        ncvar1 = datasetnc.variables[variables[0]]
        shp = ncvar1.shape
        if len(index[0]) == 1:
            ind = index[0][0]
        else:
            ind = np.asarray(range(np.min(np.min(index[0])),np.max(np.max(index[0]))))
        if len(index[1]) == 1:
            jnd = index[1][0]
        else:
            jnd = np.asarray(range(np.min(np.min(index[1])),np.max(np.max(index[1]))))
        if len(shp) > 3: # Check if the variable has depth
            #ncvar1.set_auto_maskandscale(False)
            var1 = ncvar1[t, layer[0], ind, jnd]
        elif len(shp) == 3:
            var1 = ncvar1[t, ind, jnd]
        elif len(shp) == 2:
            var1 = ncvar1[ind, jnd]
        if type(var1) == np.ndarray:
            var1 = var1.squeeze()
        if len(variables) > 1: # Check if request came with more than 1 var
            ncvar2 = datasetnc.variables[variables[1]]
            shp = ncvar2.shape
            if len(shp) > 3: # Check if the variable has depth
                #ncvar2.set_auto_maskandscale(False)
                var2 = ncvar2[t, layer[0], ind, jnd]
            elif len(shp) == 3:
                var2 = ncvar2[t, ind, jnd]
            elif len(shp) == 2:
                var2 = ncvar2[ind, jnd]
            if type(var1) == np.ndarray:
                var2 = var2.squeeze()
        else:
            var2 = None
        if special_function == "+":
            var1 = var1 + var2
            var2 = None
    return var1, var2

def plot(lon, lat, var1, var2, actions, ax, fig, **kwargs):
    aspect = kwargs.get('aspect', None)
    height = kwargs.get('height')
    width = kwargs.get('width')
    norm = kwargs.get('norm')
    cmap = get_cmap(kwargs.get('cmap', 'jet'))
    cmin = kwargs.get('cmin', "None")
    cmax = kwargs.get('cmax', "None")
    magnitude = kwargs.get('magnitude', 2)
    if var1 is not None:
        if var2 is not None:
            mag = np.sqrt(var1**2 + var2**2)
        else:
            mag = var1
        mag = mag.squeeze()
        if "pcolor" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            pcolor(lon, lat, mag, ax, cmin, cmax, cmap)
        if "facets" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            pcolor(lon, lat, mag, ax, cmin, cmax, cmap)
        elif "filledcontours" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            fcontour(lon, lat, mag, ax, norm, cmin, cmax, cmap)
        elif "contours" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            contour(lon, lat, mag, ax, norm, cmin, cmax, cmap)
        #elif "facets" in actions:
        #    fig.set_figheight(height/80.0)
        #    fig.set_figwidth(width/80.0)
        #    facet(lon, lat, mag, ax)
        elif "vectors" in actions:
            fig.set_figheight(height/80.0/aspect)
            fig.set_figwidth(width/80.0)
            vectors(lon, lat, var1, var2, mag, ax, norm, cmap, magnitude)
        elif "barbs" in actions:
            fig.set_figheight(height/80.0/aspect)
            fig.set_figwidth(width/80.0)
            barbs(lon, lat, var1, var2, mag, ax, norm, cmin, cmax, cmap, magnitude)

def pcolor(lon, lat, mag, ax, cmin, cmax, cmap):
    mag = np.ma.array(mag, mask=np.isnan(mag))
    #ax.pcolorfast(lon, lat, mag[:-1, :-1], shading="", norm=norm, cmap='jet',)
    ax.pcolormesh(lon, lat, mag, vmin=cmin, vmax=cmax, cmap=cmap)

def fcontour(lon, lat, mag, ax, norm, cmin, cmax, cmap):
    if (cmin == "None") or (cmax == "None"):
        levs = None
    else:
        levs = np.arange(1, 12)*(cmax-cmin)/10
        levs = np.hstack(([-99999], levs, [99999]))
    ax.contourf(lon, lat, mag, norm=norm, levels=levs, antialiased=True, linewidth=2, cmap=cmap)

def contour(lon, lat, mag, ax, norm, cmin, cmax, cmap):
    if (cmin == "None") or (cmax == "None"):
        levs = None
    else:
        levs = np.arange(0, 12)*(cmax-cmin)/10
    ax.contour(lon, lat, mag, norm=norm, levels=levs, antialiased=True, linewidth=2, cmap=cmap)

#def lcontour(lon, lat, var1, var2, ax): pass

#def lfcontour(lon, lat, var1, var2, ax): pass

#def facet(lon, lat, var1, var2, ax):
#    pass

def vectors(lon, lat, var1, var2, mag, ax, norm, cmap, magnitude):
    if magnitude == "True":
        arrowsize = None
    elif magnitude == "False":
        arrowsize = 2.
    elif magnitude == "None":
        arrowsize = None
    else:
        arrowsize = float(magnitude)
    stride = 1
    ax.quiver(lon[::stride,::stride], lat[::stride,::stride], var1.squeeze()[::stride,::stride], var2.squeeze()[::stride,::stride], mag.squeeze()[::stride,::stride],
                pivot='mid',
                #units='uv', #xy
                cmap=cmap,
                norm=norm,
                minlength=.5,
                scale=arrowsize,
                scale_units='inches',
                angles='uv',
                )

def barbs(lon, lat, var1, var2, mag, ax, norm, cmin, cmax, cmap, magnitude):
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

    ax.barbs(lon, lat, var1.squeeze(), var2.squeeze(), mag.squeeze(),
            length=7.,
            pivot='middle',
            barb_increments=dict(half=full/2., full=full, flag=flag),
            #units='xy',
            cmap=cmap,
            norm=norm,
            linewidth=1.7,
            sizes=dict(emptybarb=0.2, spacing=0.14, height=0.5),
            #antialiased=True
            #angles='uv',
            )
