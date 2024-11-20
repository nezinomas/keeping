from django import template

register = template.Library()


@register.inclusion_tag("core/includes/generic_form.html", takes_context=True)
def generic_form(context, title, css_class=None):
    return {
        "title": title,
        "css_class": css_class,
        "form": context.get("form"),
        "form_action": context.get("form_action", "insert"),
        "url": context.get("url", ""),
        "hx_trigger_form": context.get("hx_trigger_form", ""),
    }
