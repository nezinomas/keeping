from django import template

register = template.Library()


@register.inclusion_tag('core/includes/form_field.html')
def field(form, field, custom_class):
    return {
        'form': form,
        'field': field,
        'custom_class': custom_class if custom_class else ''
    }
