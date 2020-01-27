from django import template

register = template.Library()


@register.inclusion_tag('core/includes/cell_decimal.html')
def cell(value,
         highlight_value=False,
         text_after=None,
         text_before=None,
         width=None,
         tag='td',
         css_class=None,
         default_if_empty=None):
    return {
        'value': value,
        'highlight_value': highlight_value,
        'text_before': text_before,
        'text_after': text_after,
        'width': width,
        'tag': tag,
        'css_class': css_class,
        'default_if_empty': default_if_empty,
    }
