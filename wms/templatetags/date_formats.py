from django import template
register = template.Library()


@register.filter(name='date_format_z')
def date_format_z(ds):
    return ds.strftime("%Y-%m-%dT%H:%M:%SZ")
