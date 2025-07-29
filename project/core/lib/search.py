import argparse
import re
from functools import reduce
from operator import and_, or_

from django.db.models import Q

from ...books.models import Book
from ...expenses.models import Expense
from ...incomes.models import Income

SEARCH_DICT = {"category": None, "year": None, "month": None, "remark": None}


def sanitize_search_str(search_str):
    if search_str:
        search_str = re.sub(r"[^\w\d\.\- ]", "", search_str)

    return search_str


def parse_search_no_args(search_str):
    rtn = SEARCH_DICT.copy()

    if not search_str:
        return rtn

    if match := re.search(r"(\d{4})-{0,1}\.{0,1}(\d{0,2})", search_str):
        if match[1]:
            rtn["year"] = int(match[1])

        if match[2]:
            rtn["month"] = int(match[2])

    if match := [
        word
        for word in search_str.split(" ")
        if not any(char.isdigit() for char in word)
    ]:
        rtn["category"] = match
        rtn["remark"] = match

    return rtn


def parse_search_with_args(search_str):
    parser = argparse.ArgumentParser()
    parser.add_argument("-category", "-c", type=str, nargs="+")
    parser.add_argument("-year", "-y", type=int)
    parser.add_argument("-month", "-m", type=int)
    parser.add_argument("-remark", "-r", type=str, nargs="+")

    args = parser.parse_args(search_str.split())
    args = vars(args)

    return {key: args.get(key, SEARCH_DICT[key]) for key in SEARCH_DICT}


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
    except (AttributeError, SystemExit):
        search_dict = parse_search_no_args(_str)
        search_type = "no_args"

    search_dict = filter_short_search_words(search_dict)

    return search_dict, search_type


def _get(search_dict, key, default_value):
    try:
        value = search_dict[key]
    except KeyError:
        return default_value

    return value or default_value


def generic_search(model, search_str, category_list, date_field="date"):
    search_dict, search_type = make_search_dict(search_str)

    if all(value is None for value in search_dict.values()):
        return model.objects.none()

    query = model.objects.items()

    # Date filters
    for key in ["year", "month"]:
        if not search_dict.get(key):
            continue
        query = query.filter(**{f"{date_field}__{key}": search_dict[key]})

    # Category filters
    category_filters = [
        reduce(
            or_,
            (
                Q(**{f"{category}__icontains": search_word})
                for category in category_list
            ),
        )
        for search_word in _get(search_dict, "category", [])
    ]

    # Remark filters
    remark_filters = [
        Q(remark__icontains=search_word)
        for search_word in _get(search_dict, "remark", [])
    ]

    # Combine Category and Remark filters
    if combined_filters := category_filters + remark_filters:
        operator_ = and_ if search_type == "with_args" else or_
        query = query.filter(reduce(operator_, combined_filters))

    return query.order_by(f"{date_field}")


def search_expenses(search_str):
    category_list = ["expense_type__title", "expense_name__title"]

    return generic_search(Expense, search_str, category_list).values(
        "id",
        "date",
        "account__title",
        "expense_type__pk",
        "expense_type__title",
        "expense_name__title",
        "price",
        "quantity",
        "remark",
        "attachment",
        "exception",
    )


def search_incomes(search_str):
    category_list = ["income_type__title"]

    return generic_search(Income, search_str, category_list).values(
        "id",
        "date",
        "income_type__title",
        "account__title",
        "price",
        "remark",
    )


def search_books(search_str):
    category_list = ["author", "title"]

    return generic_search(Book, search_str, category_list, "started")
