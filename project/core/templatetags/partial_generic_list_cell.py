from django import template

register = template.Library()


@register.inclusion_tag('core/includes/partial_generic_list_cell.html')
def td(value):
    return {
        'value': value,
    }
