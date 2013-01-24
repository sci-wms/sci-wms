import netCDF4, sys, os
from rtree import index
from datetime import datetime

def build_from_nc(filename):
    timer = datetime.now()
    nc = netCDF4.Dataset(filename)
    lat = nc.variables['lat'][:]
    lon = nc.variables['lon'][:]
    latc = nc.variables['latc'][:]
    lonc = nc.variables['lonc'][:]
    nc.close()

    def generator_nodes():
        for i, coord in enumerate(zip(lon, lat, lon, lat)):
            yield(i, coord, None)

    def generator_cells():
        for i, coord in enumerate(zip(lonc, latc, lonc, latc)):
            yield(i, coord, None)

    filename = filename[:-3]
    tree = index.Index(filename+'_nodes', generator_nodes(), overwrite=True)
    print (datetime.now()-timer).seconds # How long did it take to add the points
    tree.close()
    tree = index.Index(filename+'_cells', generator_cells(), overwrite=True)
    tree.close()
    print (datetime.now()-timer).seconds # How long did it take to add the points

if __name__ == "__main__":
    filename = sys.argv[1]
    build_from_nc(filename)