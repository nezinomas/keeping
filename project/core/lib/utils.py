from typing import Dict

from .date import monthname


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(monthname(month), 0.0)) if arr else 0.0
