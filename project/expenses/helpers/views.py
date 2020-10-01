import re
from functools import reduce
from operator import or_

from django.db.models import Q

from .. import models


def parse_search_input(search_str):
    # find all 2000 or 2000-01 or 2000.01 inputs
    rgx = re.compile(r'\d{4}-{0,1}\.{0,1}\d{0,2}')

    match = re.findall(rgx, search_str)
    _date = match[0] if match else None

    searches = search_str.split(' ')

    _search = []
    for word in searches:
        if word in match:
            continue

        if len(word) >= 4:
            _search.append(word)

    return _date, _search


def search(search_str):
    _date, _search = parse_search_input(search_str)

    sql = models.Expense.objects.items()

    if _date:
        year = _date[0:4]
        sql = sql.filter(date__year=year)

        if len(_date) > 4:
            month = _date[5:]
            sql = sql.filter(date__month=month)

    if _search:
        sql = sql.filter(
            reduce(or_, (Q(expense_type__title__icontains=q) for q in _search)) |
            reduce(or_, (Q(expense_name__title__icontains=q) for q in _search)) |
            reduce(or_, (Q(remark__icontains=q) for q in _search))
        )

    sql = sql.order_by('-date')

    return sql
