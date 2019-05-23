from django import template

register = template.Library()


@register.inclusion_tag('core/includes/generic_form.html', takes_context=True)
def generic_form(context, title, update_container):
    return {
        'title': title,
        'update_container': update_container,
        'form': context['form'],
        'action': context['action'],
        'url': context['url'],
    }
