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


#--------------------------------------
#You shouldn't have to edit the below:
#--------------------------------------
import os

# Where did you put me:
fullpath_to_wms = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# local path to database (doesn't include file name)
topologypath = os.path.join(fullpath_to_wms, "topology")
if not os.path.exists(topologypath):
    os.makedirs(topologypath)

# local path to statics (doesn't include file name)
staticspath = os.path.join(fullpath_to_wms, "src/pywms/wms/static")

# mostly the below is for testing purposes only:
# if this is populated, the service will use the dataset above for schema/grid information
# and the dataset below for actual data extraction.
localdataset = False
localpath = {
    '30yr_gom3' : "/home/user/Data/FVCOM/gom3_197802.nc",

    }
