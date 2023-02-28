from django import template
from slippers.templatetags.slippers import register_components

register = template.Library()

register_components(
    {
        "new_count_button": "counts/new_count_button.html",
    },
    register,
)
