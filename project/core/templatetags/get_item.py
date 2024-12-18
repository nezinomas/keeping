from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0) if dictionary else None


@register.filter
def get_obj_attr(obj, attr):
    # print(f'--------------------------->\n{obj=} {attr=}\n')
    _attr = None
    try:
        _attr = getattr(obj, attr)
    except (AttributeError, TypeError):
        _attr = attr
    # print(f'--------------------------->\n{_attr=}\n')
    return _attr


@register.filter
def get_list_val(arr: list, key: int):
    try:
        val = arr[key]
    except (KeyError, IndexError, TypeError):
        val = None

    return val
