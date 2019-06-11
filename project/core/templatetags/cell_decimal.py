from django import template

register = template.Library()


@register.inclusion_tag('core/includes/cell_decimal.html')
def td(value, width='7%'):
    return {
        'value': value,
        'width': width,
    }
