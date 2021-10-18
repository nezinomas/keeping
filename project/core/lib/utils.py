from collections import Counter
from typing import Any, Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.query import QuerySet

from .date import monthname


def get_user():
    request = CrequestMiddleware.get_request()
    return request.user


def get_request_kwargs(name):
    request = None
    try:
        request = CrequestMiddleware.get_request().resolver_match.kwargs.get(name)
    except:
        pass

    return request


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(monthname(month), 0.0)) if arr else 0.0


def sum_all(arr: List[Dict]) -> Dict:
    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    rtn = Counter()

    for row in arr:
        try:
            rtn.update(row)
        except TypeError:
            pass

    return {**rtn}


def sum_col(arr: List[Dict], key: Any) -> float:
    rtn = sum_all(arr)

    return rtn.get(key, 0.0)
