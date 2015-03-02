'''
COPYRIGHT 2010 RPS ASA

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

import sys
import netCDF4
from rtree import index
from datetime import datetime


def build_from_nc(dataset):

    nc = netCDF4.Dataset(dataset.topology_file)
    try:
        if nc.grid == 'cgrid':
            lat = nc.variables['lat'][:]
            lon = nc.variables['lon'][:]

            def generator_nodes():
                c = -1
                for row in range(lon.shape[0]):
                    for col in range(lon.shape[1]):
                        coord = (lon[row, col], lat[row, col], lon[row, col], lat[row, col],)
                        c += 1
                        yield(c, coord, ((row,), (col,)))

            tree = index.Index(dataset.node_tree_root, generator_nodes(), overwrite=True)
            tree.close()
        else:
            lat = nc.variables['lat'][:]
            lon = nc.variables['lon'][:]
            latc = nc.variables['latc'][:]
            lonc = nc.variables['lonc'][:]
            nv = nc.variables['nv'][:]  # (3, long)

            # Nodes
            tree = index.Index(dataset.node_tree_root, overwrite=True, pagesize=2**17)
            for i, coord in enumerate(zip(lon, lat, lon, lat)):
                tree.insert(i, coord, None)
            tree.close()

            # Cells
            tree = index.Index(dataset.cell_tree_root, overwrite=True, pagesize=2**17)
            for i, coord in enumerate(zip(lonc, latc, lonc, latc)):
                tree.insert(i, coord, (lon[nv[:, i]-1], lat[nv[:, i]-1],))
            tree.close()
    finally:
        nc.close()

if __name__ == "__main__":
    filename = sys.argv[1]
    build_from_nc(filename)
