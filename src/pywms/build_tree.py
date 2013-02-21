import netCDF4, sys, os
from rtree import index
from datetime import datetime

def build_from_nc(filename):
    timer = datetime.now()
    nc = netCDF4.Dataset(filename)
    if nc.grid == 'cgrid':
        lat = nc.variables['lat'][:]
        lon = nc.variables['lon'][:]
        nc.close()
        #print lon.shape
        def generator_nodes():
            c = -1
            for row in range(lon.shape[0]):
                for col in range(lon.shape[1]):
                    coord = (lon[row,col], lat[row,col], lon[row,col], lat[row,col],)
                    c += 1
                    yield(c, coord, ((row,), (col,)))

        filename = filename[:-3]
        tree = index.Index(filename+'_nodes', generator_nodes(), overwrite=True)
        #print (datetime.now()-timer).seconds # How long did it take to add the points
        tree.close()
    else:
        lat = nc.variables['lat'][:]
        lon = nc.variables['lon'][:]
        latc = nc.variables['latc'][:]
        lonc = nc.variables['lonc'][:]
        nv = nc.variables['nv'][:] # (3, long)
        #print nv.shape, lonc.shape
        nc.close()

        def generator_nodes():
            for i, coord in enumerate(zip(lon, lat, lon, lat)):
                yield(i, coord, None)

        def generator_cells():
            for i, coord in enumerate(zip(lonc, latc, lonc, latc)):
                yield( i, coord, (lon[nv[:,i]-1], lat[nv[:,i]-1],) )

        filename = filename[:-3]
        tree = index.Index(filename+'_nodes', generator_nodes(), overwrite=True)
        #print (datetime.now()-timer).seconds # How long did it take to add the points
        tree.close()
        tree = index.Index(filename+'_cells', generator_cells(), overwrite=True)
        tree.close()
        #print (datetime.now()-timer).seconds # How long did it take to add the points

if __name__ == "__main__":
    filename = sys.argv[1]
    build_from_nc(filename)
