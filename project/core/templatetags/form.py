from django import template

register = template.Library()


@register.inclusion_tag('expenses/includes/generic_form.html', takes_context=True)
def generic_form(context, title):
    return {
        'title': title,
        'form': context['form'],
        'submit_title': context['action']
    }
