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
    'global' : "http://www.smast.umassd.edu:8080/thredds/dodsC/models/fvcom/GLOBAL/GLOB_1977_08.nc",
    'adcirc' : "http://opendap.renci.org:1935/thredds/dodsC/tc/debby/17/ultralite/blueridge.renci.org/asgs1/nhcConsensus/fort.63.nc",
    # "dataset_id3":"path or OpenDAP endpoint",
    }
    
#---------------------------------------------------------
    
    
    
    
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
    '30yr_gom3':"/home/acrosby/Development/Data/FVCOM/gom3_197802.nc",

    }


    
