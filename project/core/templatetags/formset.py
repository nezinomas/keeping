from django import template

register = template.Library()


@register.inclusion_tag('core/includes/generic_formset.html', takes_context=True)
def generic_formset(context, title):
    return {
        'title': title,
        'formset': context['formset'],
        'shared_form': context['shared_form'],
        'form_action': context['form_action'],
        'submit_button': context.get('submit_button'),
        'url': context['url'],
    }
