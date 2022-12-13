from collections import Counter
from decimal import Decimal
from typing import Any, Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.query import QuerySet

from .date import monthname


def get_user():
    request = CrequestMiddleware.get_request()
    return request.user


def get_request_kwargs(name):
    crequest = CrequestMiddleware.get_request()
    if not crequest:
        return None

    try:
        return crequest.resolver_match.kwargs.get(name)
    except KeyError:
        return None


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(monthname(month), 0.0)) if arr else 0.0


def sum_all(arr, keys=None):
    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    result = Counter()
    for item in arr:
        for k, v in item.items():
            if isinstance(v, (int, float, Decimal)) and (keys is None or k in keys):
                result[k] += v
    return dict(result)


def sum_col(arr: List[Dict], key: Any) -> float:
    rtn = sum_all(arr)

    return rtn.get(key, 0.0)


def getattr_(obj, name, default=None):
    try:
        return getattr(obj, name)
    except AttributeError:
        return default
