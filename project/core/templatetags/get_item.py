from typing import Any, Dict

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
def get_sum(dict_: Dict, month: int):
    dt = dict_.get('date')
    if dt:
        d = dt.month
        if d == month:
            return dict_.get('sum')
