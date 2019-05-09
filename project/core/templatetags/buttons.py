from django import template

register = template.Library()


@register.inclusion_tag('core/includes/button_delete.html')
def button_delete(*args, **kwargs):
    return {
        'pk': kwargs['pk'] if 'pk' in kwargs else None,
        'url': kwargs['url'] if 'url' in kwargs else None,
        'tbl': kwargs['tbl'] if 'tbl' in kwargs else None,
        'label': kwargs['label'] if 'label' in kwargs else None,
        'type': kwargs['type']
    }


@register.inclusion_tag('core/includes/button_update.html')
def button_update(*args, **kwargs):
    return {
        'pk': kwargs['pk'],
        'tbl': kwargs['tbl'],
        'label': kwargs['label'] if 'label' in kwargs else None,
    }


@register.inclusion_tag('core/includes/button_close.html')
def button_close(*args, **kwargs):
    return {
        'pk': kwargs['pk'],
        'tbl': kwargs['tbl'],
        'label': kwargs['label'] if 'label' in kwargs else None,
    }


@register.inclusion_tag('core/includes/button_edit.html')
def button_edit(*args, **kwargs):
    return {
        'pk': kwargs['pk'],
        'url': kwargs['url'],
        'tbl': kwargs['tbl'],
        'label': kwargs['label'] if 'label' in kwargs else None,
    }


@register.inclusion_tag('core/includes/button_create.html')
def button_create(*args, **kwargs):
    return {
        'url': kwargs['url'],
        'label': kwargs['label'],
        'tbl': kwargs['tbl'],
        'width': kwargs['width'] if 'width' in kwargs else None
    }


@register.inclusion_tag('core/includes/button_quick_update.html')
def button_quick_update(*args, **kwargs):
    return {
        'pk': kwargs['pk'],
        'url': kwargs['url'],
        'tbl': kwargs['tbl'],
        'label': kwargs['label'] if 'label' in kwargs else None,
    }
