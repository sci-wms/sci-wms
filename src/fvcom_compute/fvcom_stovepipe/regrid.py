'''
Created on Sep 23, 2011

@author: ACrosby
'''
import numpy
import shapely.geometry as geometry
import pp

def regrid(trivals, trilon, trilat, topology, reglon, reglat, size):
    #import pprocess
    ppservers = ()
    reglon, reglat = numpy.meshgrid(reglon, reglat)
    reglon = numpy.reshape(reglon, numpy.prod(numpy.shape(reglon)))
    reglat = numpy.reshape(reglat, numpy.prod(numpy.shape(reglat)))
    
    def newvalues(lon, lat, size, tri, trivals):
        new = createNewCell(lon, lat, size)
        matches = searchForIntersect(tri, new)
        if len(matches) > 0:
            supergrid = createIntersections(tri, matches, new)
            #matched = [tri[match] for match in matches]
            #sdists = findDistancesList(getCentroid(supergrid), getCentroid(matched))
            sareas = findVolumesList(supergrid)
            matched = [trivals[match] for match in matches]
            newvalue = getNewCellValue(new, matched, 5, sareas)
        else: newvalue = -9999
        return newvalue
    
    tri = createPolygonList(trilon, trilat, topology)
    #parallel = pprocess.Map(limit=2)
    #pnewvalues = parallel.manage(pprocess.MakeParallel(newvalues))
    job_server = pp.Server(20, ppservers=ppservers)
    parallel = []
    for i in range(len(reglon)):
        parallel.append(job_server.submit(newvalues, (reglon[i], reglat[-(i+1)], size, tri, trivals),
                                      (createNewCell, searchForIntersect, createIntersections,
                                       findDistancesList, getCentroid, findVolumesList,
                                       getNewCellValue, haversine), ("shapely.geometry as geometry", "numpy",)))
    
    ##parallel = [newvalues(reglon[i], reglat[i], size, tri, trivals) for i in range(len(reglon))]
    parallel = [i() for i in parallel]
    return parallel                               
    
def createNewCell(lon, lat, size):
    newcell = geometry.Polygon(((lon+(size/2), lat+(size/2)),
                      (lon+(size/2), lat-(size/2)),
                      (lon-(size/2), lat-(size/2)),
                      (lon-(size/2), lat+(size/2)))) 
    return newcell
   

def createPolygonList(lon, lat, topology):
    '''
    Create a list of polygons from input unstructured topology array
    '''
    #def seq(a, lon, lat):
    #    return numpy.asarray((lon[a[0]], lat[a[0]]), 
    #            (lon[a[1]], lat[a[1]]), 
    #            (lon[a[2]], lat[a[2]]))
    #ringsequence = numpy.apply_along_axis(seq, 0, topology, lon, lat)
    polygons = []
    for i in range(len(topology[:,1])):
        polygon = geometry.Polygon(((lon[topology[i,0]],lat[topology[i,0]]),
                                   (lon[topology[i,1]],lat[topology[i,1]]),
                                   (lon[topology[i,2]],lat[topology[i,2]])))
        polygons.append(polygon)
        
    #polygons = map(geometry.Polygon, ringsequence)
    return polygons

def searchForIntersect(polygonlist, newcell):
    '''
    Return a list of indices corresponding to the polygons that intersect
    with the select polygon
    '''
    def all_indices(value, qlist):
        indices = []
        idx = -1
        while 1:
            try:
                idx = qlist.index(value, idx+1)
                indices.append(idx)
            except ValueError:
                break
        return indices
    isintersect = [polygon.intersects(newcell) for polygon in polygonlist]
    intersection_indices = all_indices(True, isintersect)
    return intersection_indices

def createIntersections(polygons, intersections, newcell):
    '''
    Create new supergrid polygons from intersections and return them as a
    list of polygons
    '''
    polygons = [polygons[i] for i in intersections]
    supergrid = [polygon.intersection(newcell) for polygon in polygons]
    return supergrid

def findDistancesList(original_centroids, supergrid_centroids):
    '''
    Input dictionaries of supergrid centroids and original intersect polygon
    centroids, and return a list of distances. Using a haversine calculation
    to determine distance.
    '''
    dists = map(haversine, [o.y for o in original_centroids],
                [o.x for o in original_centroids], 
                [s.y for s in supergrid_centroids], 
                [s.x for s in supergrid_centroids])
    return dists

def findVolumesList(polygons):
    '''
    Return the calculated areas of the input list of polygons.
    '''
    area = [polygon.area for polygon in polygons]
    #area = polygons.area
    return area

def getNewCellValue(newcell, svalues, sdists, sareas):
    '''
    Return a value for a new cell using inputs of list of values, list of
    distances, and list of areas for supergrid cells, and volume of the new cell
    '''
    newvalue = numpy.sum((numpy.asarray(svalues)) * numpy.asarray(sareas)) / newcell.area
    return newvalue

def getCentroid(polygons):
    '''
    Calculate the location of the centroids of the list of input polygons
    and return them as a list of dictionaries with fields x and y
    '''
    points = [polygon.centroid for polygon in polygons]
    #points = polygons.centroid
    return points

def haversine(lat1, lon1, lat2, lon2):
    import math
    # Haversine formulation
    # inputs in degrees
    startX = math.radians(lon1)
    startY = math.radians(lat1)
    endX = math.radians(lon2)
    endY = math.radians(lat2)
    diffX = endX - startX
    diffY = endY - startY
    a = math.sin(diffY/2)**2 + math.cos(startY) * math.cos(endY) * math.sin(diffX/2)**2
    c = 2 * math.atan2(math.sqrt(a),  math.sqrt(1-a))
    length = 6371 * c
    return length




