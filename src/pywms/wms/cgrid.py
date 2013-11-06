'''
COPYRIGHT 2010 Alexander Crosby

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

#cgrid
#import os, sys
import numpy as np
from matplotlib.pylab import get_cmap
from matplotlib.mlab import griddata
import ugrid
import time as timeobj

def subset(latmin, lonmin, latmax, lonmax, lat, lon):
    #t1 = timeobj.time()
    latbool = (lat <= latmax+.18) & (lat >= latmin-.18)
    lonbool = (lon <= lonmax+.18) & (lon >= lonmin-.18)
    index = np.asarray(np.where(latbool & lonbool)).squeeze()
        #((lat <= latmax) == (lat >= latmin)) ==
        #((lon <= lonmax) == (lon >= lonmin),))).squeeze()
    #if (lonmax > 0) & (lonmin < 0):
    #    lon[lon > lonmax+30] = np.nan # would prefer to be subsetting the smallest area possible isntead of just hacking the rendering...
    #    lon[lon < lonmin-30] = np.nan
    if index.shape[1] > 0:
        ind = np.asarray(range(np.min(np.min(index[0])),np.max(np.max(index[0]))+1))
        jnd = np.asarray(range(np.min(np.min(index[1])),np.max(np.max(index[1]))+1))
        lat = lat[ind[0]:ind[-1], jnd[0]:jnd[-1]]
        lon = lon[ind[0]:ind[-1], jnd[0]:jnd[-1]]
    else:
        index = None
        lat = np.asarray([[],[]])
        lon = np.asarray([[],[]])
    #print str(timeobj.time()-t1) + " subset coords"
    return index, lat, lon

def getvar(datasetnc, t, layer, variables, index):
    #t1 = timeobj.time()
    special_function = ""
    if index is None:
        var1 = None
        var2 = None
        var3 = None
    else:
        if "+" in variables[0]:
            variables = variables[0].split("+")
            special_function = "+"
        if "*" in variables[0]:
            variables = variables[0].split("*")
            special_function = "*"
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
            var1 = ncvar1[t, [layer], ind, jnd]
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
                var2 = ncvar2[t, [layer], ind, jnd]
            elif len(shp) == 3:
                var2 = ncvar2[t, ind, jnd]
            elif len(shp) == 2:
                var2 = ncvar2[ind, jnd]
            if type(var1) == np.ndarray:
                var2 = var2.squeeze()
        else:
            var2 = None
        
        if len(variables) > 2: # Check if request came with more than 1 var
            ncvar3 = datasetnc.variables[variables[2]]
            shp = ncvar3.shape
            if len(shp) > 3: # Check if the variable has depth
                #ncvar2.set_auto_maskandscale(False)
                var3 = ncvar3[t, [layer], ind, jnd]
            elif len(shp) == 3:
                var3 = ncvar3[t, ind, jnd]
            elif len(shp) == 2:
                var3 = ncvar3[ind, jnd]
            if type(var1) == np.ndarray:
                var3 = var3.squeeze()
        else:
            var3 = None
        
        if special_function == "+":
            #var1[np.isnan(var2)] = np.nan # not causing it and probably slowing things down
            #var2[np.isnan(var1)] = np.nan
            var1 = var1 + var2
            var2 = None
        if special_function == "*":
            var1 = var1.squeeze()
            if len(var1.shape) > 1:
                alpha = np.ones_like(var1)
                try:
                    alpha[var1.mask] = 0
                    alpha[(var1==0)&(var2.squeeze()==0)&(var3.squeeze()==0)] = 0
                except:
                    pass
                var1 = np.asarray((var1, var2.squeeze(), var3.squeeze(), alpha))
                var2 = var3 = None
            else:
                var1 = var2 = var3 = None
        if var1 != None:
            if "additional_fill_values" in ncvar1.ncattrs():
                for fillval in map(float, ncvar1.additional_fill_values.split(",")):
                    #temp = var1==fillval
                    #var1.mask[var1==fillval] = True
                    var1[var1==fillval] = np.nan
        if var2 != None:
            if "additional_fill_values" in ncvar2.ncattrs():
                for fillval in map(float, ncvar2.additional_fill_values.split(",")):
                    var2[var2==fillval] = np.nan
    #print str(timeobj.time()-t1) + " dap"
    return var1, var2

def plot(lon, lat, var1, var2, actions, ax, fig, **kwargs):
    #t1 = timeobj.time()
    aspect = kwargs.get('aspect', None)
    height = kwargs.get('height')
    width = kwargs.get('width')
    norm = kwargs.get('norm')
    cmap = get_cmap(kwargs.get('cmap', 'jet'))
    cmin = kwargs.get('cmin', "None")
    cmax = kwargs.get('cmax', "None")
    magnitude = kwargs.get('magnitude', 'False')
    if var1 is not None:
        if var2 is not None:
            mag = np.sqrt(var1**2 + var2**2)
        else:
            if magnitude == 'False':
                mag = var1
            else:
                mag = np.abs(var1)
        mag = mag.squeeze()
        if "composite" in actions or mag.shape[0] == 3:
            m = kwargs.get('basemap')
            lonmin = kwargs.get("lonmin")
            latmin = kwargs.get("latmin")
            lonmax = kwargs.get("lonmax")
            latmax = kwargs.get("latmax")
            projection = kwargs.get("projection")
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            composite(lon, lat, mag, ax, cmin, cmax, cmap, m, fig, lonmin, latmin, lonmax, latmax, projection, height, width)
        elif "pcolor" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            pcolor(lon, lat, mag, ax, cmin, cmax, cmap, norm)
        elif "pcolorraw" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            pcolorraw(lon, lat, mag, ax, cmin, cmax, cmap, norm)
        elif "facets" in actions:
            fig.set_figheight(height/80.0)
            fig.set_figwidth(width/80.0)
            pcolor(lon, lat, mag, ax, cmin, cmax, cmap, norm)
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
        elif "unitvectors" in actions:
            fig.set_figheight(height/80.0/aspect)
            fig.set_figwidth(width/80.0)
            unit_vectors(lon, lat, var1, var2, mag, ax, norm, cmap, magnitude)
        elif "streamlines" in actions:
            fig.set_figheight(height/80.0/aspect)
            fig.set_figwidth(width/80.0)
            m = kwargs.get('basemap')
            lonmin = kwargs.get("lonmin")
            latmin = kwargs.get("latmin")
            lonmax = kwargs.get("lonmax")
            latmax = kwargs.get("latmax")
            streamlines(lon, lat, var1, var2, mag, ax, norm, cmap, magnitude, m, lonmin, latmin, lonmax, latmax)
        elif "barbs" in actions:
            fig.set_figheight(height/80.0/aspect)
            fig.set_figwidth(width/80.0)
            barbs(lon, lat, var1, var2, mag, ax, norm, cmin, cmax, cmap, magnitude)
    #print str(timeobj.time()-t1) + " plot"

def composite(lon, lat, mag, ax, cmin, cmax, cmap, m, fig, lonmin, latmin, lonmax, latmax, projection, height, width):
    mag = np.transpose(mag, axes=(1,2,0)).astype(float)
    mag[:,:,0:3] = mag[:,:,0:3] / 255.
    lonmax, latmax = m(lonmax, latmax)
    lonmin, latmin = m(lonmin, latmin)
    #print m.llcrnry, m.llcrnrx, m.urcrnry, m.urcrnrx, mag[:,:,1].max().max(), mag[:,:,1].min().min() 
    ex = np.asarray([((lon.min()-lonmin+1)/(lonmax-lonmin))*m.urcrnrx, ((lon.max()-lonmin+1)/(lonmax-lonmin))*m.urcrnrx,((lat.min()-latmin+1)/(latmax-latmin))*m.urcrnry,((lat.max()-latmin+1)/(latmax-latmin))*m.urcrnry])
    m.ax.imshow(mag, origin='lower',
                extent=ex)
    
def pcolor(lon, lat, mag, ax, cmin, cmax, cmap, norm):
    mag = np.ma.array(mag, mask=np.isnan(mag))
    if (cmin == "None") or (cmax == "None"):
        cmin, cmax = mag.min(), mag.max()
    lon = np.ma.asarray(lon)
    lat = np.ma.asarray(lat)
    isn = np.ma.getmaskarray(lon) + np.ma.getmaskarray(lat)
    if (isn > 0).any():
        mask = mag.mask
        xymask = (isn[0:-1, 0:-1] + isn[1:, 1:] +
                  isn[0:-1, 1:] + isn[1:, 0:-1])
        mask[0:-1, 0:-1] = mask[0:-1, 0:-1] + xymask
        mask[1:, 1:] = mask[1:, 1:] + xymask
        mask[0:-1, 1:] = mask[0:-1, 1:] + xymask
        mask[1:, 0:-1] = mask[1:, 0:-1] + xymask
        mag = np.ma.array(mag, mask=mask)
    #ax.pcolorfast(lon, lat, mag[:-1, :-1], shading="", norm=norm, cmap='jet',)
    ax.pcolormesh(lon, lat, mag, vmin=cmin, vmax=cmax, cmap=cmap, norm=norm)

def pcolorraw(lon, lat, mag, ax, cmin, cmax, cmap, norm):
    mag = np.ma.array(mag, mask=np.isnan(mag))
    if (cmin == "None") or (cmax == "None"):
        cmin, cmax = mag.min(), mag.max()
    #ax.pcolorfast(lon, lat, mag[:-1, :-1], shading="", norm=norm, cmap='jet',)
    ax.pcolor(lon, lat, mag, vmin=cmin, vmax=cmax, cmap=cmap, norm=norm)

def fcontour(lon, lat, mag, ax, norm, cmin, cmax, cmap):
    if (cmin == "None") or (cmax == "None"):
        levs = None
    else:
        levs = np.arange(1, 12)*(cmax-cmin)/10
        levs = np.hstack(([-99999], levs, [99999]))
    shp = lon.shape
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
                
def unit_vectors(lon, lat, var1, var2, mag, ax, norm, cmap, magnitude):
    if magnitude == "True":
        arrowsize = None
    elif magnitude == "False":
        arrowsize = 2.
    elif magnitude == "None":
        arrowsize = None
    else:
        arrowsize = float(magnitude)
    stride = 1
    theta = np.degrees(np.arctan(var2/var1))
    var1 = np.cos(np.radians(theta))# u
    var2 = np.sin(np.radians(theta))# v
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
                
def streamlines(lon, lat, var1, var2, mag, ax, norm, cmap, magnitude, m, lonmin, latmin, lonmax, latmax):
    if magnitude == "True":
        arrowsize = None
    elif magnitude == "False":
        arrowsize = 2.
    elif magnitude == "None":
        arrowsize = None
    else:
        arrowsize = float(magnitude)
    stride = 1
    try:
        ax.streamplot(lon[::stride,::stride], lat[::stride,::stride], 
                      var1.squeeze()[::stride,::stride], var2.squeeze()[::stride,::stride], 
                      color=mag.squeeze()[::stride,::stride],
                      density=6,
                      linewidth=5*mag.squeeze()[::stride,::stride]/mag.squeeze()[::stride,::stride].max(),
                      cmap=cmap,
                      norm=norm,
                      )
    except:
        num = int( (lonmax - lonmin) * 50000)#320 )
        xi = np.arange(m.xmin, m.xmax, num)
        yi = np.arange(m.ymin, m.ymax, num)
        lat, lon, mag, var1, var2 = lat.astype(np.float64).flatten(), lon.astype(np.float64).flatten(), mag.astype(np.float64).flatten(), var1.astype(np.float64).flatten(), var2.astype(np.float64).flatten()
        print lat.shape, mag.shape, var1.shape
        mag = griddata(lon, lat, mag, xi, yi, interp='nn')
        var1 = griddata(lon, lat, var1, xi, yi, interp='nn')
        var2 = griddata(lon, lat, var2, xi, yi, interp='nn')
        ax.streamplot(xi, yi, 
                      var1, var2, 
                      color=mag,
                      density=6,
                      linewidth=5*mag/mag.max(),
                      cmap=cmap,
                      norm=norm,
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
