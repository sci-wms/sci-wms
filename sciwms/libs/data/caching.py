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

Created on Sep 6, 2011

@author: ACrosby

!!!THIS IS NOT A SCRIPT ANYMORE!!!
'''
from dateutil.parser import parse
from netCDF4 import Dataset as ncDataset
from netCDF4 import date2num
import sys
import os
import numpy
import tempfile
import traceback
from datetime import datetime
import numpy as np
from wms.models import Dataset
from sciwms.libs.data import build_tree
from collections import deque
import shutil
try:
    import cPickle as pickle
except:
    import pickle as pickle

from django.conf import settings
from sciwms import logger
from pyugrid import UGrid
from utils import get_nc_variable_values
from custom_exceptions import deprecated, NonCompliantDataset

time_units = 'hours since 1970-01-01'


def create_domain_polygon(dataset):
    from shapely.geometry import Polygon
    from shapely.ops import cascaded_union

    nc = ncDataset(dataset.topology_file)
    nv = nc.variables['nv'][:, :].T-1
    #print np.max(np.max(nv))
    latn = nc.variables['lat'][:]
    lonn = nc.variables['lon'][:]
    lon = nc.variables['lonc'][:]
    lat = nc.variables['latc'][:]
    #print lat, lon, latn, lonn, nv
    index_pos = numpy.asarray(numpy.where(
        (lat <= 90) & (lat >= -90) &
        (lon <= 180) & (lon > 0),)).squeeze()
    index_neg = numpy.asarray(numpy.where(
        (lat <= 90) & (lat >= -90) &
        (lon < 0) & (lon >= -180),)).squeeze()
    #print np.max(np.max(nv)), np.shape(nv), np.shape(lonn), np.shape(latn)
    if len(index_pos) > 0:
        p = deque()
        p_add = p.append
        for i in index_pos:
            flon, flat = lonn[nv[i, 0]], latn[nv[i, 0]]
            lon1, lat1 = lonn[nv[i, 1]], latn[nv[i, 1]]
            lon2, lat2 = lonn[nv[i, 2]], latn[nv[i, 2]]
            if flon < -90:
                flon = flon + 360
            if lon1 < -90:
                lon1 = lon1 + 360
            if lon2 < -90:
                lon2 = lon2 + 360
            p_add(Polygon(((flon, flat),
                           (lon1, lat1),
                           (lon2, lat2),
                           (flon, flat),)))
        domain_pos = cascaded_union(p)
    if len(index_neg) > 0:
        p = deque()
        p_add = p.append
        for i in index_neg:
            flon, flat = lonn[nv[i, 0]], latn[nv[i, 0]]
            lon1, lat1 = lonn[nv[i, 1]], latn[nv[i, 1]]
            lon2, lat2 = lonn[nv[i, 2]], latn[nv[i, 2]]
            if flon > 90:
                flon = flon - 360
            if lon1 > 90:
                lon1 = lon1 - 360
            if lon2 > 90:
                lon2 = lon2 - 360
            p_add(Polygon(((flon, flat),
                           (lon1, lat1),
                           (lon2, lat2),
                           (flon, flat),)))
        domain_neg = cascaded_union(p)
    if len(index_neg) > 0 and len(index_pos) > 0:
        from shapely.prepared import prep
        domain = prep(cascaded_union((domain_neg, domain_pos,)))
    elif len(index_neg) > 0:
        domain = domain_neg
    elif len(index_pos) > 0:
        domain = domain_pos
    else:
        logger.info(nc.__str__())
        logger.info(lat)
        logger.info(lon)
        logger.error("Domain file creation - No data in topology file Length of positive:%u Length of negative:%u" % (len(index_pos), len(index_neg)))
        raise ValueError("No data in file")

    f = open(dataset.domain_file, 'w')
    pickle.dump(domain, f)
    f.close()
    nc.close()
