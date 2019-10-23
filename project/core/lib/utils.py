from typing import Any, Dict, List
from django.db.models.query import QuerySet
from .date import monthname


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(monthname(month), 0.0)) if arr else 0.0


def sum_col(arr: List[Dict], key: Any) -> float:
    rtn = 0.0

    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    for row in arr:
        try:
            rtn += float(row[key])
        except:
            break

    return rtn


def sum_all(arr: List[Dict]) -> Dict:
    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    d = {}

    if not arr:
        return d

    keys = arr[0].keys()
    for key in keys:
        d[key] = sum_col(arr, key)

    return d
