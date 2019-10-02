from typing import Dict

from .date import month_name


def get_value_from_dict(arr: Dict, month: int) -> float:
    return float(arr.get(month_name(month), 0.0)) if arr else 0.0
