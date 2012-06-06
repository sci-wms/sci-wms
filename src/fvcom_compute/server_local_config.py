
#
#
#

# local path to database (doesn't include file name)
dbpath = "/home/acrosby/Development/Python/unstructured_server/fvcom_wms/src/"
topologypath = "/home/acrosby/Development/Python/unstructured_server/fvcom_wms/src/fvcom_compute/topology.nc"

# local path to statics (doesn't include file name)
staticspath = "/home/acrosby/Development/Python/unstructured_server/fvcom_wms/src/fvcom_compute/fvcom_stovepipe/static/"

# local path to dataset (includes filename)
datasetpath = "http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3"


# if this is populated, the service will use the dataset above for schema/grid information
# and the dataset below for actual data extraction.
localdataset = True

localpath = "/home/acrosby/Development/Data/FVCOM/gom3_197802.nc"

localhostip = "192.168.100.146:7000"
    
