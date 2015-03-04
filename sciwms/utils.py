'''
Created on Mar 3, 2015

@author: ayan
'''
import pyproj


class CoordinateSystem(object):
    
    def __init__(self, projection='EPSG:3857'):
        self.proj_str = '+init={0}'.format(projection)
        self.proj_sys = pyproj.Proj(self.proj_str)
        
    def geographic_to_projected(self, x_val, y_val):
        projected_coordinates = self.proj_sys(x_val, y_val)
        return projected_coordinates
    
    def projected_to_geographic(self, x_val, y_val):
        geographic_coordinates = self.proj_sys(x_val, y_val, inverse=True)
        return geographic_coordinates
    
    
def create_coordinate_param(xmin, ymin, xmax, ymax):
    coord_str = '{xmin},{ymin},{xmax},{ymax}'.format(ymin=ymin, xmin=xmin, ymax=ymax, xmax=xmax)
    return coord_str
    