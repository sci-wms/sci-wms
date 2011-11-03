# Configuration for the deployment specific settings of the 
# unstructured services. 
#
#
#
#

# local path to database (doesn't include file name)
dbpath = "C:/Documents and Settings/ACrosby/My Documents/Eclipse/fvcom_compute/src/"

# local path to statics (doesn't include file name)
staticspath = "C:/Documents and Settings/ACrosby/My Documents/Eclipse/unstructured_sura/src/fvcom_compute/fvcom_stovepipe/static/"

# local path to dataset (includes filename)
datasetpath = "http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3"
#datasetpath = "http://localhost:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3"


# if this is populated, the service will use the dataset above for schema/grid information
# and the dataset below for actual data extraction.
localdataset = True
localpath = "E:\FVCOM\gom3_197802.nc"
#localpath = "/home/acrosby/Development/Data/FVCOM/gom3_197802.nc"

