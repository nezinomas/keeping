from django import template

register = template.Library()


@register.inclusion_tag("bookkeeping/includes/detailed_table.html", takes_context=True)
def detailed_table(context, name, items, total, total_col, total_row):
    return {
        "name": name,
        "items": items,
        "total": total,
        "total_row": total_row,
        "total_col": total_col,
        "month_names": context.get("month_names"),
    }
