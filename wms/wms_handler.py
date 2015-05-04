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

Created on Oct 17, 2011

@author: ACrosby
'''
from datetime import date

class wms_handler(object):
    '''
    classdocs
    '''
    def make_action_request(self, requestobj):
        layers = requestobj.GET["layers"]
        try:
            levels = requestobj.GET["elevation"]
            if levels == "":
                levels = "0"
        except:
            levels = "0"
        '''
        Implement more styles and things here
        '''
        try:
            time = requestobj.GET["time"]
            if time == "":
                now = date.today().isoformat()
                time = now + "T00:00:00"#
        except:
            now = date.today().isoformat()
            time = now + "T00:00:00"#
        time = time.split("/")
        for i in range(len(time)):
            #print time[i]
            time[i] = time[i].replace("Z", "")
            if len(time[i]) == 16:
                time[i] = time[i] + ":00"
            elif len(time[i]) == 13:
                time[i] = time[i] + ":00:00"
            elif len(time[i]) == 10:
                time[i] = time[i] + "T00:00:00"
        if len(time) > 1:
            timestart = time[0]
            timeend = time[1]
        else:
            timestart = time[0]
            timeend = time[0]
        box = requestobj.GET["bbox"]
        box = box.split(",")
        latmin = box[1]  # ymin
        latmax = box[3]  # ymax
        lonmin = box[0]  # xmin
        lonmax = box[2]  # xmax

        height = requestobj.GET["height"]
        width = requestobj.GET["width"]

        # start handling of styles
        styles = requestobj.GET["styles"].split(",")[0].split("_")
        colormap = '_'.join(styles[1:])
        image_type = styles[0]
        # end handling of styles

        climits = (None, None)
        if 'colorscalerange' in requestobj.GET:
            try:
                climits = map(lambda x: float(x), requestobj.GET["colorscalerange"].split(','))
            except:
                pass

        tempget = requestobj.GET.copy()
        tempget.clear()
        values = {
                    u'latmax':       latmax,
                    u'lonmax':       lonmax,
                    u'projection':   u'merc',
                    u'layer':        levels,
                    u'datestart':    timestart,
                    u'dateend':      timeend,
                    u'lonmin':       lonmin,
                    u'latmin':       latmin,
                    u'height':       height,
                    u'width':        width,
                    u'actions':      ("image," + "," + styles[0] + "," + styles[1]),  #
                    u'colormap':     colormap,
                    u'climits':      climits,
                    u'image_type':   image_type,
                    u'variables':    layers,
                    u'topologytype': 'node',
                    u'magnitude':    'normal'
                 }
        for k, v in values.iteritems():
            tempget[k] = v
        requestobj.GET = tempget.copy()

        if float(lonmax)-float(lonmin) < .0001:
            requestobj = None
        return requestobj

    def __init__(self, requestobj):
        '''
        Constructor
        '''
        self.request = requestobj
