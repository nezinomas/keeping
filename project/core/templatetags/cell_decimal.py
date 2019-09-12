from django import template

register = template.Library()


@register.inclusion_tag('core/includes/cell_decimal.html')
def td(value, text=None, negative=False, positive=False, width=None):
    return {
        'value': value,
        'width': width,
        'negative': negative,
        'positive': positive,
        'text': text
    }
