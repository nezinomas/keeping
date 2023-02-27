from collections import Counter
from typing import Any, Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.query import QuerySet


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


def clean_year_picker_input(field_name, data, cleaned_data, errors):
    # ugly workaround for YearPickerInput field
    # widget returns YYYY-01-01 instead YYYY
    # is it possible to change backend_date_format?
    field = data.get(field_name)
    if not field:
        return cleaned_data
    # try split field by '-'
    try:
        field, *_ = field.split("-")
    except AttributeError:
        return cleaned_data
    # try convert field to int
    try:
        int(field)
    except ValueError:
        return cleaned_data
    # if field is in past
    if int(field) < 1974:
        return cleaned_data
    # if error for field exists in errors
    if errors.get(field_name):
        cleaned_data[field_name] = field
        errors.pop(field_name)

    return cleaned_data
