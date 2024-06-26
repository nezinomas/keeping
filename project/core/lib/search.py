import argparse
import re
from functools import reduce
from operator import and_, or_

from django.db.models import Q

from ...books.models import Book
from ...expenses.models import Expense
from ...incomes.models import Income


def sanitize_search_str(search_str):
    if search_str:
        search_str = re.sub(r"[^\w\d\.\- ]", "", search_str)

    return search_str


def parse_search_input(search_str):
    _date = None
    _search = []

    search_str = sanitize_search_str(search_str)

    if not search_str:
        return _date, _search

    # find all 2000 or 2000-01 or 2000.01 inputs
    rgx = re.compile(r"\d{4}-{0,1}\.{0,1}\d{0,2}")

    match = re.findall(rgx, search_str)
    _date = match[0] if match else None

    searches = search_str.split(" ")

    _search = []
    for word in searches:
        if word in match:
            continue

        if len(word) >= 2:
            _search.append(word)

    return _date, _search


def parse_search_no_args(search_str):
    rtn = {"category": None, "year": None, "month": None, "remark": None}

    if match := re.search(r"(\d{4})-{0,1}\.{0,1}(\d{0,2})", search_str):
        if match[1]:
            rtn["year"] = int(match[1])

        if match[2]:
            rtn["month"] = int(match[2])

    if match := [word for word in search_str.split(" ") if not any(char.isdigit() for char in word)]:
        rtn["category"] = match
        rtn["remark"] = match

    return rtn


def parse_search_with_args(search_str):
    parser = argparse.ArgumentParser()
    parser.add_argument('-category', '-c', type=str, nargs='+')
    parser.add_argument('-year', '-y', type=int)
    parser.add_argument('-month', '-m', type=int)
    parser.add_argument('-remark', '-r', type=str, nargs='+')

    args = parser.parse_args(search_str.split())

    return vars(args)


def filter_short_search_words(search_dict):
    def filter_words(words):
        return [word for word in words if len(word) > 2]

    for key in ["category", "remark"]:
        if search_dict[key] is None:
            continue

        search_dict[key] = filter_words(search_dict[key])

    return search_dict


def make_search_dict(search_str):
    _str = sanitize_search_str(search_str)

    try:
        search_dict = parse_search_with_args(_str)
        search_type = "with_args"
    except SystemExit:
        search_dict = parse_search_no_args(_str)
        search_type = "no_args"

    search_dict = filter_short_search_words(search_dict)

    return search_dict, search_type


def filter_dates(_date, sql, field="date"):
    if _date:
        year = _date[:4]
        sql = sql.filter(**{f"{field}__year": year})

        if len(_date) > 4:
            month = _date[5:]
            sql = sql.filter(**{f"{field}__month": month})

    return sql


def _get(search_dict, key, default_value=None):
    if default_value is None:
        default_value = []

    try:
        value = search_dict[key]
    except KeyError:
        return default_value

    return value or default_value


def search_expenses(search_str):
    search_dict, search_type = make_search_dict(search_str)

    if all(value is None for value in search_dict.values()):
        return Expense.objects.none()

    query = Expense.objects.items()

    date_filters = {
        "year": "date__year",
        "month": "date__month"
    }

    for key, filter_key in date_filters.items():
        if search_dict[key]:
            query = query.filter(**{filter_key: search_dict[key]})

    category_filters = [
        Q(expense_type__title__icontains=q) | Q(expense_name__title__icontains=q)
        for q in _get(search_dict, "category")
    ]

    remark_filters = [
        Q(remark__icontains=q)
        for q in _get(search_dict, "remark")
    ]

    if combined_filters := category_filters + remark_filters:
        operator_ = and_ if search_type == 'with_args' else or_
        query = query.filter(reduce(operator_, combined_filters))

    query = query.order_by("-date")

    return query


def search_incomes(search_str):
    _sql = Income.objects.none()
    _date, _search = parse_search_input(search_str)

    if _date or _search:
        _sql = Income.objects.items()
        _sql = filter_dates(_date, _sql)

        if _search:
            _sql = _sql.filter(
                reduce(or_, (Q(income_type__title__icontains=q) for q in _search))
                | reduce(or_, (Q(remark__icontains=q) for q in _search))
            )

        _sql = _sql.order_by("-date")

    return _sql


def search_books(search_str):
    _sql = Book.objects.none()
    _date, _search = parse_search_input(search_str)

    if _date or _search:
        _sql = Book.objects.items()
        _sql = filter_dates(_date, _sql, "started")

        if _search:
            _sql = _sql.filter(
                reduce(or_, (Q(author__icontains=q) for q in _search))
                | reduce(or_, (Q(title__icontains=q) for q in _search))
                | reduce(or_, (Q(remark__icontains=q) for q in _search))
            )

        _sql = _sql.order_by("-started")

    return _sql
