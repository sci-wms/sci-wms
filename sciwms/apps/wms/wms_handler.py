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
        #print time
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
        latmin = box[1]
        latmax = box[3]
        lonmin = box[0]
        lonmax = box[2]

        height = requestobj.GET["height"]
        width = requestobj.GET["width"]
        styles = requestobj.GET["styles"].split(",")[0].split("_")

        colormap = styles[2].replace("-", "_")
        climits = styles[3:5]
        topology_type = styles[5]
        magnitude_bool = styles[6]

        requestobj._set_get( {u'latmax':latmax, u'lonmax':lonmax,
                          u'projection':u'merc', u'layer':levels,
                          u'datestart':timestart, u'dateend':timeend,
                          u'lonmin':lonmin, u'latmin':latmin,
                          u'height':height, u'width':width,
                          u'actions':("image," + \
                          "," + styles[0] + "," + styles[1]),
                          u'colormap': colormap,
                          u'climits': climits,
                          u'variables': layers,
                          u'topologytype': topology_type,
                          u'magnitude': magnitude_bool,
                          } )
        if float(lonmax)-float(lonmin) < .0001:
            requestobj == None
        return requestobj



    def __init__(self, requestobj):
        '''
        Constructor
        '''
        self.request = requestobj
