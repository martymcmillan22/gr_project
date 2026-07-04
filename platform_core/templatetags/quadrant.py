from django import template

from platform_core.resolvers.quadrant import resolve_url


register = template.Library()


@register.simple_tag(name="quadrant_url")
def quadrant_url(hour=None, pm=None):
    return resolve_url(hour=hour, pm=pm)