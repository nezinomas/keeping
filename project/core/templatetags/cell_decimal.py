from django import template

register = template.Library()


@register.inclusion_tag('core/includes/cell_decimal.html')
def td(
    value,
    text_after=None, text_before=None,
    negative=False, positive=False,
    width=None, tag='td'
):
    return {
        'value': value,
        'width': width,
        'tag': tag,
        'negative': negative,
        'positive': positive,
        'text_after': text_after,
        'text_before': text_before,
    }
