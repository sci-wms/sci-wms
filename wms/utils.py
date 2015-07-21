# -*- coding: utf-8 -*-
import numpy as np

from wms import logger


def get_layer_from_request(dataset, request):
    # Find the layer we are working with
    requested_layers = request.GET.get('layers')
    if not requested_layers:
        # For GetLegendGraphic requests
        requested_layers = request.GET.get('layer')
        if not requested_layers:
            requested_layers = request.GET.get("query_layers")
    layer_objects = dataset.layer_set.filter(var_name=requested_layers)
    virtuallayer_objects = dataset.virtuallayer_set.filter(var_name=requested_layers)
    try:
        return (list(layer_objects) + list(virtuallayer_objects))[0]
    except IndexError:
        raise ValueError("No layer or virtuallayer named {} found on dataset".format(requested_layers))
    
    
def adjacent_array_value_differences(np_array):
    """
    Calculate the differences between
    adjacent values in a numpy array.
    
    """
    a_1 = np_array[..., 1:]
    a_0 = np_array[..., :-1]
    delta_a = a_0 - a_1
    return delta_a


def calc_lon_lat_padding(lon_array, lat_array, safety_factor=10):
    """
    Calculate the padding to be used when
    determining a spatial index. A fudge factor
    is applied to ensure that the necessary data
    is grab. 
    
    This is particularly useful when plotting
    vectors, as they may be cut off depending on the
    scale used. Having a larger padding means
    that a tile is initially created with data
    that exists in another tile before being trimed
    to size. This avoids the appearance of seems
    in tile layer responses.
    
    """
    delta_lon = adjacent_array_value_differences(lon_array)
    delta_lat = adjacent_array_value_differences(lat_array.T)
    average_delta_lon = np.average(delta_lon)
    average_delta_lat = np.average(delta_lat)
    abs_avg_delta_lon = np.absolute(average_delta_lon)
    abs_avg_delta_lat = np.absolute(average_delta_lat)
    if abs_avg_delta_lon > abs_avg_delta_lat:
        calculated_padding = abs_avg_delta_lon * safety_factor
    else:
        calculated_padding = abs_avg_delta_lat * safety_factor
    return calculated_padding
    
    
def calc_safety_factor(requested_vector_scale):
    """
    Calculate an appropriate fudge factor
    based on vector_scale. Smaller requested_vector_scale
    will require a larger fudge factor.
    
    """
    # figured out this function by inspection
    sf = 802 * requested_vector_scale ** -1.453
    if sf < 10:
        return 10
    else:
        return sf
    

def find_appropriate_time(var_obj, time_variables):
    """
    If there a multiple variables with standard_name = time,
    find the appropriate to be used with a layer. If one cannot
    be found, raise an exception.

    """
    if hasattr(var_obj, 'coordinates'):
        coordinates = set(var_obj.coordinates.split(' '))
    dimensions = set(var_obj.dimensions)
    time_set = set([v.name for v in time_variables])
    c_intersects = list(coordinates.intersection(time_set))
    d_intersects = list(dimensions.intersection(time_set))
    if len(c_intersects) > 0:
        return c_intersects[0]
    elif len(d_intersects) > 0:
        return d_intersects[0]
    else:
        raise ValueError('Unable to determine an appropriate variable to use as time.')


class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)
