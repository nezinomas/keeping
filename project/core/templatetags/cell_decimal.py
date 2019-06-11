from django import template

register = template.Library()


@register.inclusion_tag('core/includes/cell_decimal.html')
def td(value):
    return {
        'value': value,
    }
