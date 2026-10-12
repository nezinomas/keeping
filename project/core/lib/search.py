import argparse
import re
from functools import reduce
from operator import and_, or_

from django.db.models import Q


def _empty_search():
    return {"category": [], "year": 0, "month": 0, "remark": []}


def parse_search(search_str):
    """The fields, and how terms combine: flags by `and_`, plain words by `or_`."""
    _str = _sanitize_search_str(search_str)

    try:
        search_dict = _parse_search_with_args(_str)
        combine = and_
    except NotFlagsError:
        search_dict = _parse_search_no_args(_str)
        combine = or_

    return _filter_short_search_words(search_dict), combine


def _sanitize_search_str(search_str):
    return re.sub(r"[^\w\d\.\- ]", "", search_str)


def _parse_search_no_args(search_str):
    rtn = _empty_search()

    if match := re.search(r"(\d{4})-{0,1}\.{0,1}(\d{0,2})", search_str):
        rtn["year"] = int(match[1])
        rtn["month"] = int(match[2] or 0)

    words = [
        word for word in search_str.split() if not any(char.isdigit() for char in word)
    ]
    rtn["category"] = words
    rtn["remark"] = words

    return rtn


class NotFlagsError(ValueError):
    """The search text is plain words, not flags."""


class SilentArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise NotFlagsError(message)


def _parse_search_with_args(search_str):
    parser = SilentArgumentParser(add_help=False)
    parser.add_argument("-category", "-c", type=str, nargs="+")
    parser.add_argument("-year", "-y", type=int)
    parser.add_argument("-month", "-m", type=int)
    parser.add_argument("-remark", "-r", type=str, nargs="+")
    parser.set_defaults(**_empty_search())

    return vars(parser.parse_args(search_str.split()))


def _filter_short_search_words(search_dict):
    for key in ["category", "remark"]:
        search_dict[key] = [word for word in search_dict[key] if len(word) > 2]

    return search_dict


def generic_search(query, search_str, category_list, date_field="date"):
    search_dict, combine = parse_search(search_str)

    if not any(search_dict.values()):
        return query.none()

    query = _apply_date_filters(query, search_dict, date_field)

    combined_filters = _build_category_filters(search_dict, category_list)
    combined_filters += _build_remark_filters(search_dict)

    if combined_filters:
        query = query.filter(reduce(combine, combined_filters))

    return query.order_by(f"-{date_field}")


def _apply_date_filters(query, search_dict, date_field):
    for key in ["year", "month"]:
        if not search_dict[key]:
            continue
        query = query.filter(**{f"{date_field}__{key}": search_dict[key]})
    return query


def _build_category_filters(search_dict, category_list):
    return [
        reduce(
            or_,
            (
                Q(**{f"{category}__icontains": search_word})
                for category in category_list
            ),
        )
        for search_word in search_dict["category"]
    ]


def _build_remark_filters(search_dict):
    return [Q(remark__icontains=search_word) for search_word in search_dict["remark"]]
