from django import template

register = template.Library()


@register.inclusion_tag("plans/includes/generic_list.html")
def generic_list(year, items, type=None, expense_type=None, update=None, delete=None):
    return {
        "year": year,
        "items": items,
        "type": type,
        "expense_type": "expense_type" if expense_type else None,
        "update": update,
        "delete": delete,
    }
