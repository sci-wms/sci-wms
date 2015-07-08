# -*- coding: utf-8 -*-

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
