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


@register.inclusion_tag("core/includes/generic_delete_form.html", takes_context=True)
def generic_delete_form(context, title):
    return {
        "title": title,
        "url": context.get("url"),
        "object": context.get("object"),
        "hx_trigger_form": context.get("hx_trigger_form", ""),
    }
