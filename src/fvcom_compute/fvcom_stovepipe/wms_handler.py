'''
Created on Oct 17, 2011

@author: ACrosby
'''

class wms_handler(object):
    '''
    classdocs
    '''

    def make_action_request(self, requestobj):

        layers = requestobj.GET["LAYERS"]
        levels = requestobj.GET["ELEVATION"]
        '''
        Implement more styles and things here
        '''
        time = requestobj.GET["TIME"]
        time = time.split("/")
        if len(time) > 1: 
            timestart = time[0]
            timeend = time[1]
        else:
            timestart = time[0]
            timeend = time[0]
        box = requestobj.GET["BBOX"]
        box = box.split(",")
        latmin = box[1]
        latmax = box[3]
        lonmin = box[0]
        lonmax = box[2]
        height = requestobj.GET["HEIGHT"]
        width = requestobj.GET["WIDTH"]
        
        class action_request:
            pass
        action_request.GET = {u'latmax':latmax, u'lonmax':lonmax,
                          u'projection':u'merc', u'layer':levels,
                          u'datestart':timestart, u'dateend':timeend,
                          u'lonmin':lonmin, u'latmin':latmin,
                          u'height':height, u'width':width,
                          u'actions':("image," + layers), }
        return action_request
                
        

    def __init__(self, requestobj):
        '''
        Constructor
        '''
        self.request = requestobj