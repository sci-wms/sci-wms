
#--------------------------------------
#You shouldn't have to edit the below:
#--------------------------------------
import os

# Where did you put me:
fullpath_to_wms = os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))

# local path to database (doesn't include file name)
topologypath = os.path.join(fullpath_to_wms,
    "src/pywms/")

# local path to statics (doesn't include file name)
staticspath = os.path.join(fullpath_to_wms,
    "src/pywms/wms/static")

# mostly the below is for testing purposes only:
# if this is populated, the service will use the dataset above for schema/grid information
# and the dataset below for actual data extraction.
localdataset = False
localpath = {
    '30yr_gom3':"/home/user/Data/FVCOM/gom3_197802.nc",

    }


    
