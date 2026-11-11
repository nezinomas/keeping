from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return (dictionary or {}).get(key, 0)


@register.filter
def get_list_val(arr: list, key: int):
    val = 0
    try:
        val = arr[key]
    except (KeyError, IndexError, TypeError):
        pass

    return val
