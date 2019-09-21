from django import template

register = template.Library()


@register.inclusion_tag('core/includes/generic_formset.html', takes_context=True)
def generic_formset(context, title, update_container):
    return {
        'title': title,
        'update_container': update_container,
        'formset': context['formset'],
        'action': context['action'],
        'url': context['url'],
    }
