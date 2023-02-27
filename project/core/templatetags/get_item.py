from typing import Dict, List

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0) if dictionary else None


@register.filter
def get_obj_attr(obj, attr):
    _attr = None
    try:
        _attr = getattr(obj, attr)
    except (AttributeError, TypeError):
        _attr = attr

    return _attr


@register.filter
def get_sum_by_month(lst: List[Dict], month: int):
    for _dict in lst:
        if dt := _dict.get('date'):
            if dt.month == month:
                return _dict.get('sum')


@register.filter
def get_sum_by_title(lst: List[Dict], title: str):
    for _dict in lst:
        _title = _dict.get('title')
        if _title == title:
            return _dict.get('sum')


@register.filter
def get_list_val(arr: List, key: int):
    try:
        val = arr[key]
    except (KeyError, IndexError, TypeError):
        val = None

    return val
