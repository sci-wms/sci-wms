from django.http import HttpResponse
import numpy
from matplotlib import pyplot as Plot ###
from mpl_toolkits.basemap import Basemap ###
#from StringIO import StringIO
#import math
#import netCDF4
from matplotlib.collections import PolyCollection
import matplotlib.tri as Tri
            
def reorderArray(values, numsrow, numscol):
        grid = [];
        for i in range(numsrow):
            grid.append(values[ (i * numscol):((i * numscol) + (numscol - 1)) ])
        return grid

def __main__( request, actions, u, v, width, height, lonmax, lonmin, latmax, latmin, index, lon, lat, lonn, latn, nv):
    fig = Plot.figure(dpi=150, facecolor='none', edgecolor='none')
    fig.set_alpha(0)
    #ax = fig.add_subplot(111)
    projection = request.GET["projection"]
    m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
                urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
                #lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
                lat_ts = 0.0,
                )
    #lonn, latn = m(lonn, latn)
    m.ax = fig.add_axes([0, 0, 1, 1])
    #fig.set_figsize_inches((20/m.aspect, 20.))
    fig.set_figheight(5)
    fig.set_figwidth(5/m.aspect)
    if "regrid" in actions:
        #import fvcom_compute.fvcom_stovepipe.regrid as regrid
        #wid = numpy.max((width, height))
        #size = (lonmax - lonmin) / wid
        #hi = (latmax - latmin) / size
        #hi = math.ceil(hi)
        #reglon = numpy.linspace(numpy.negative(lonmin), numpy.negative(lonmax), wid)
        #reglon = numpy.negative(reglon)
        #reglat = numpy.linspace(latmin, latmax, hi)

        #if "pcolor" in actions:
        #    mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
        #    mag = numpy.sqrt(mag)
        #    newvalues = regrid.regrid(mag, lonn, latn, nv, reglon, reglat, size)
        #    reglon, reglat = numpy.meshgrid(reglon, reglat)
        #    grid = reorderArray(newvalues, len(reglat[:,1]), len(reglon[1,:]))
        #    ax = fig.add_subplot(111)
        #    ax.pcolor(reglon, reglat, grid)
        #if "contours" in actions:
        #    mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
        #    mag = numpy.sqrt(mag)
        #    newvalues = regrid.regrid(mag, lonn, latn, nv, reglon, reglat, size)
        #    reglon, reglat = numpy.meshgrid(reglon, reglat)
        #    grid = reorderArray(newvalues, len(reglat[:,1]), len(reglon[1,:]))
        #    ax = fig.add_subplot(111)
        #    ax.contourf(reglon, reglat, grid)
        #if "vectors" in actions:
        #    newv = regrid.regrid(v, lonn, latn, nv, reglon, reglat, size)
        #    newu = regrid.regrid(u, lonn, latn, nv, reglon, reglat, size)
        #    mag = numpy.power(newu.__abs__(), 2)+numpy.power(newv.__abs__(), 2)
        #    mag = numpy.sqrt(mag)
        #    ax = fig.add_subplot(111)
        #    ax.quiver(reglon, reglat, newu, newv, mag, pivot='mid')
        pass
    else:
        if "vectors" in actions:
            mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
            mag = numpy.sqrt(mag)
            #ax = fig.add_subplot(111)
            #ax.quiver(lon, lat, u, v, mag, pivot='mid')
            lon, lat = m(lon, lat)
            m.quiver(lon, lat, u, v, mag, pivot='mid')
            ax = Plot.gca()
        elif "contours" in actions:
            mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
            mag = numpy.sqrt(mag)
            ax = fig.add_subplot(111)
            ax.tricontourf(lon, lat, mag)
            
        elif  "facets" in actions:
            #projection = request.GET["projection"]
            #m = Basemap(llcrnrlon=lonmin, llcrnrlat=latmin, 
            #            urcrnrlon=lonmax, urcrnrlat=latmax, projection=projection,
            #            lat_0 =(latmax + latmin) / 2, lon_0 =(lonmax + lonmin) / 2, 
            #            )
            lonn, latn = m(lonn, latn)
            #m.ax = fig.add_axes([0, 0, 1, 1])
            
            #fig.set_figheight(20)
            #fig.set_figwidth(20/m.aspect)
            #m.drawmeridians(numpy.arange(0,360,1), color='0.5',)
            tri = Tri.Triangulation(lonn,latn,triangles=nv)
            
            mag = numpy.power(u.__abs__(), 2)+numpy.power(v.__abs__(), 2)
            mag = numpy.sqrt(mag)
            #ax.tripcolor(lon, lat, mag, shading="")
            #collection = PolyCollection(numpy.asarray([(lonn[node1],latn[node1]),(lonn[node2],latn[node2]),(lonn[node3],latn[node3])]))
            verts = numpy.concatenate((tri.x[tri.triangles][...,numpy.newaxis],\
                                    tri.y[tri.triangles][...,numpy.newaxis]), axis=2)
            collection = PolyCollection(verts)
            collection.set_array(mag)
            collection.set_edgecolor('none') 
            
            ax = Plot.gca()
            
            #m.add_collection(collection)
            #ax = Plot.gca()
            #m2.ax.add_collection(collection)
            ax.add_collection(collection)

    lonmax, latmax = m(lonmax, latmax)
    lonmin, latmin = m(lonmin, latmin)
    ax.set_xlim(lonmin, lonmax)
    ax.set_ylim(latmin, latmax)
    ax.set_frame_on(False)
    ax.set_clip_on(False)
    ax.set_position([0,0,1,1])
    #Plot.yticks(visible=False)
    #Plot.xticks(visible=False)
    
    #Plot.axis('off')

    canvas = Plot.get_current_fig_manager().canvas

    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
                
    return response