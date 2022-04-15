import re
from functools import reduce
from operator import or_

from django.db.models import Q

from ...books.models import Book
from ...expenses.models import Expense
from ...incomes.models import Income


def sanitize_search_str(search_str):
    search_str = re.sub("[^\w\d\.\- ]", "", search_str)
    return search_str


def parse_search_input(search_str):
    search_str = sanitize_search_str(search_str)

    # find all 2000 or 2000-01 or 2000.01 inputs
    rgx = re.compile(r'\d{4}-{0,1}\.{0,1}\d{0,2}')

    match = re.findall(rgx, search_str)
    _date = match[0] if match else None

    searches = search_str.split(' ')

    _search = []
    for word in searches:
        if word in match:
            continue

        if len(word) >= 2:
            _search.append(word)

    return _date, _search


def filter_dates(_date, sql, field='date'):
    if _date:
        year = _date[0:4]
        sql = sql.filter(**{f'{field}__year': year})

        if len(_date) > 4:
            month = _date[5:]
            sql = sql.filter(**{f'{field}__month': month})

    return sql


def search_expenses(search_str):
    _date, _search = parse_search_input(search_str)

    sql = Expense.objects.items()
    sql = filter_dates(_date, sql)

    if _search:
        sql = sql.filter(
            reduce(or_, (Q(expense_type__title__icontains=q) for q in _search)) |
            reduce(or_, (Q(expense_name__title__icontains=q) for q in _search)) |
            reduce(or_, (Q(remark__icontains=q) for q in _search))
        )

    sql = sql.order_by('-date')

    return sql


def search_incomes(search_str):
    _date, _search = parse_search_input(search_str)

    sql = Income.objects.items()
    sql = filter_dates(_date, sql)

    if _search:
        sql = sql.filter(
            reduce(or_, (Q(income_type__title__icontains=q) for q in _search)) |
            reduce(or_, (Q(remark__icontains=q) for q in _search))
        )

    sql = sql.order_by('-date')

    return sql


def search_books(search_str):
    _date, _search = parse_search_input(search_str)

    sql = Book.objects.items()
    sql = filter_dates(_date, sql, 'started')

    if _search:
        sql = sql.filter(
            reduce(or_, (Q(author__icontains=q) for q in _search)) |
            reduce(or_, (Q(title__icontains=q) for q in _search)) |
            reduce(or_, (Q(remark__icontains=q) for q in _search))
        )

    sql = sql.order_by('-started')

    return sql
