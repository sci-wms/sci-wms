# -*- coding: utf-8 -*-


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
    try:
        var_c = var_obj.coordinates
    except AttributeError:
        # if variable doesn't have a coordinates attribute, try going through the dimensions
        # maybe the variable has the same name as a dimension (e.g. a coordinate variable)
        var_c = var_obj.dimensions
    else:
        var_c = var_c.split(' ')
    dim_set = set(var_c)
    time_set = set(time_variables)
    intersects = list(dim_set.intersection(time_set))
    if len(intersects) == 1:
        return intersects[0]
    else:
        raise ValueError('Unable to determine an appropriate variable to use as time.')
    

class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)
