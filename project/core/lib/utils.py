from collections import Counter
from typing import Any, Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.query import QuerySet


def get_user():
    request = CrequestMiddleware.get_request()
    return request.user


def get_request_kwargs(name):
    crequest = CrequestMiddleware.get_request()
    return crequest.resolver_match.kwargs.get(name) if crequest else None


def sum_all(arr, keys=None):
    if isinstance(arr, QuerySet):
        arr = [*arr.values()]

    result = Counter()
    for item in arr:
        for k, v in item.items():
            if isinstance(v, (int, float)) and (keys is None or k in keys):
                result[k] += v
    return dict(result)


def sum_col(arr: List[Dict], key: Any) -> float:
    rtn = sum_all(arr)

    return rtn.get(key, 0)


def total_row(data, fields) -> dict:
    row = {field: sum(getattr(d, field, 0) for d in data) for field in fields}

    if not row.get("profit_proc"):
        return row

    incomes = row.get("incomes", 0)
    fee = row.get("fee", 0)
    market_value = row.get("market_value", 0)

    row["profit_proc"] = ((market_value - fee) / incomes * 100) - 100 if incomes else 0

    return row