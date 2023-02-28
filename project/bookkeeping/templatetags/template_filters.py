from django import template

register = template.Library()


@register.filter
def weekend(value, css_class):
    if value == "":
        return ""

    if int(value) in (0, 6):
        return css_class

    return ""
