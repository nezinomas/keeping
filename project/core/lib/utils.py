from collections import Counter
from typing import Any, Dict, List

from django.db.models.query import QuerySet

from .date import monthname


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(monthname(month), 0.0)) if arr else 0.0


def sum_all(arr: List[Dict]) -> Dict:
    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    d = Counter()
    {d.update(row) for row in arr}

    return d


def sum_col(arr: List[Dict], key: Any) -> float:
    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    rtn = sum_all(arr)

    return rtn.get(key, 0.0)
