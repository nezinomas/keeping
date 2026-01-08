from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='inject_url')
def inject_url(template, url):
    return mark_safe(template.replace("[[url]]", str(url))) if template else ""