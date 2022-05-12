from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.inclusion_tag('core/includes/generic_form.html', takes_context=True)
def generic_form(context, title):
    form_action = context.get('form_action', 'insert')

    return {
        'title': title,
        'form': context['form'],
        'submit_button': _(form_action.title()),
        'form_action': form_action,
        'url': context.get('url', ''),
        'hx_trigger_form': context.get('hx_trigger_form', ''),
    }


@register.inclusion_tag('core/includes/generic_delete_form.html', takes_context=True)
def generic_delete_form(context, title):
    return {
        'title': title,
        'url': context['url'] if 'url' in context else '',
        'object': context['object'] if 'object' in context else '',
        'hx_trigger_form': context.get('hx_trigger_form', ''),
    }
