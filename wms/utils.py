# -*- coding: utf-8 -*-


def get_layer_from_request(dataset, request):
    # Find the layer we are working with
    requested_layers = request.GET.get('layers')

    layer_objects = dataset.layer_set.filter(var_name=requested_layers)
    virtuallayer_objects = dataset.virtuallayer_set.filter(var_name=requested_layers)

    return (list(layer_objects) + list(virtuallayer_objects))[0]


class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)
