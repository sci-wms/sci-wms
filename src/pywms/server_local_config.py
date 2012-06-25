# Please edit the following parameters to setup your pywms
# server.
# 
# Example:
#
#  localhostip = "mydomain.org:8080"
# 
#  datasetpath = {
#                  'fvcom', "http://dapserver/thredds/dodsC/my_fvcom",
#                  'adcirc', "http://dapserver/thredds/dodsC/my_adcirc",
#                  'ike', "http://dapserver/thredds/dodsC/inundation_ike",
#                }
#---------------------------------------------------------
                              
localhostip = "192.168.100.146:7000" # the ip or domain and port
                                     # that you are trying to bind
                                     # the service to
                                     # this is used for the "wmstest" page
                                     
# Where are the datasets that you want to serve?
datasetpath = {
    '30yr_gom3':"http://www.smast.umassd.edu:8080/thredds/dodsC/fvcom/hindcasts/30yr_gom3",
    'forecast' : "http://www.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/Forecasts/NECOFS_GOM3_FORECAST.nc",

    # "dataset_id":"path or OpenDAP endpoint",
    # "dataset_id2":"path or OpenDAP endpoint",
    # "dataset_id3":"path or OpenDAP endpoint",
    }
    
#---------------------------------------------------------
    
    
    
    
#--------------------------------------
#You shouldn't have to edit the below:
#--------------------------------------
import os

# Where did you put me:
fullpath_to_wms = os.path.abspath("../..")

# local path to database (doesn't include file name)
topologypath = os.path.join(fullpath_to_wms,
    "src/pywms/")

# local path to statics (doesn't include file name)
staticspath = os.path.join(fullpath_to_wms,
    "src/pywms/fvcom_stovepipe/static/")

# mostly the below is for testing purposes only:
# if this is populated, the service will use the dataset above for schema/grid information
# and the dataset below for actual data extraction.
localdataset = False
localpath = {
    '30yr_gom3':"/home/acrosby/Development/Data/FVCOM/gom3_197802.nc",

    }


    
