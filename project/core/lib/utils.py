from typing import Any, Dict, List

from .date import monthname


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(monthname(month), 0.0)) if arr else 0.0


def sum_col(arr: List[Dict], key: Any) -> Dict:
    return sum(x[key] for x in arr)


def sum_all(arr: List[Dict]) -> Dict:
    d = {}
    keys = arr[0].keys()
    for key in keys:
        d[key] = sum_col(arr, key)

    return d
