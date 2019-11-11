from typing import Any, Dict, List

from django import template

register = template.Library()


@register.filter
def get_obj_attr(obj, attr):
    _attr = None
    try:
        _attr = getattr(obj, attr)
    except Exception as ex:
        _attr = attr

    return _attr


@register.filter
def get_dict_val(obj: Dict, key: Any):
    _key = None
    try:
        _key = obj.get(key, key)
    except Exception as ex:
        _key = key

    return _key


@register.filter
def get_sum_by_month(lst: List[Dict], month: int):
    for _dict in lst:
        dt = _dict.get('date')
        if dt:
            if dt.month == month:
                return _dict.get('sum')


@register.filter
def get_sum_by_title(lst: List[Dict], title: str):
    for _dict in lst:
        _title = _dict.get('title')
        if _title == title:
            return _dict.get('sum')
