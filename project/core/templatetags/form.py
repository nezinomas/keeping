from django import template

register = template.Library()


@register.inclusion_tag('core/includes/generic_form.html', takes_context=True)
def generic_form(context, title, update_container, chained_dropdown=None):
    return {
        'title': title,
        'update_container': update_container,
        'form': context['form'],
        'action': context['action'] if 'action' in context else '',
        'url': context['url'] if 'url' in context else '',
        'chained_dropdown': chained_dropdown
    }


@register.inclusion_tag('core/includes/generic_delete_form.html', takes_context=True)
def generic_delete_form(context, title, update_container):
    return {
        'title': title,
        'update_container': update_container,
        'action': context['action'] if 'action' in context else '',
        'url': context['url'] if 'url' in context else '',
        'object': context['object'] if 'object' in context else '',
    }
