from isodate.isostrf import strftime, D_DEFAULT

from django import template
register = template.Library()


@register.filter(name='date_format_z')
def date_format_z(ds):
    return ds.strftime("%Y-%m-%dT%H:%M:%SZ")


@register.filter(name='class_name')
def class_name(ds):
    return ds.__class__.__name__


@register.filter(name='triple_period_format_z')
def triple_period_format_z(ds):
    ws = []
    for w in ds:
        ws.append('/'.join([w[0].isoformat(), w[1].isoformat(), strftime(w[2], D_DEFAULT)]))
    return ','.join(ws)


@register.filter(name='sciwms_version')
def sciwms_version():
    from wms.utils import version
    return version()
