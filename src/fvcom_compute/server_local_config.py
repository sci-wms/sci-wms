
#
#
#
# the ip or domain and port that you are trying to bind the service to
# this is used for the wmstest page
localhostip = "192.168.100.146:7000"

# local path to database (doesn't include file name)
dbpath = "/home/acrosby/Development/Python/unstructured_server/fvcom_wms/src/"
topologypath = "/home/acrosby/Development/Python/unstructured_server/fvcom_wms/src/fvcom_compute/"

# local path to statics (doesn't include file name)
staticspath = "/home/acrosby/Development/Python/unstructured_server/fvcom_wms/src/fvcom_compute/fvcom_stovepipe/static/"

# local path to dataset (includes filename) OR Opendap endpoint
datasetpath = {
    '30yr_gom3':"http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3",
    'mass_bay':"http://www.smast.umassd.edu:8080/thredds/dodsC/models/fvcom/NECOFS/Forecasts/NECOFS_FVCOM_OCEAN_MASSBAY_FORECAST.nc",
    'necofs_wave' : "http://www.smast.umassd.edu:8080/thredds/dodsC/models/fvcom/NECOFS/Forecasts/NECOFS_WAVE_FORECAST.nc",
    'gom3_forecast' : "http://www.smast.umassd.edu:8080/thredds/dodsC/models/fvcom/NECOFS/Forecasts/NECOFS_GOM3_FORECAST.nc",
    'adcirc' : "http://testbedapps-dev.sura.org/thredds/dodsC/in/und/adcirc/ike/ultralite/lr/vardrag/nowave/3d",
    }

# mostly the below is for testing purposes only:
# if this is populated, the service will use the dataset above for schema/grid information
# and the dataset below for actual data extraction.
localdataset = False

localpath = {
    '30yr_gom3':"/home/acrosby/Development/Data/FVCOM/gom3_197802.nc",

    }


    
