import json
from django.http import HttpResponse


def from_dict(d):    
    response = HttpResponse(content_type='application/json')
    response.write(json.dumps(d, sort_keys=True, separators=(',', ':')))
    return response
