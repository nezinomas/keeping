from django import template

register = template.Library()


@register.filter
def weekend(value, css_class):
    if value == "":
        return ""

    return css_class if int(value) in {0, 6} else ""
