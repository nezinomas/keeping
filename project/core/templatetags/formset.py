from django import template

register = template.Library()


@register.inclusion_tag('core/includes/generic_formset.html', takes_context=True)
def generic_formset(context, title, update_container):
    return {
        'title': title,
        'update_container': update_container,
        'formset': context['formset'],
        'from_action': context['from_action'],
        'submit_button': context.get('submit_button'),
        'url': context['url'],
    }
