from datetime import date

import factory
import pytest
from django.db.models.signals import post_save

from ...models import Expense
from ...services.search import search_expenses, search_totals
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "_search, expect",
    [
        (
            "1999",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-y 1999",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        ("1999.1", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("1999-1", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("-y 1999 -m 1", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("3000", []),
        ("a", []),
        ("ab", []),
        (
            "type_a",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-c type_a",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "type_a name_b",
            [
                {"type": "Type_B", "name": "Name_B", "remark": "WWW"},
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-c type_a name_b",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
            ],
        ),
        (
            "type_a xxx",
            [
                {"type": "Type_A", "name": "Name_B", "remark": "YYY"},
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        ("-c type_a -r xxx", [{"type": "Type_A", "name": "Name_A", "remark": "XXX"}]),
        ("-c type_a name_a -r www", []),
        (
            "-c type_a name_a -r xxx",
            [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "1999 name_a",
            [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        (
            "-y 1999 -c name_a",
            [
                {"type": "Type_A", "name": "Name_A", "remark": "XXX"},
            ],
        ),
        pytest.param(
            "-c žvaigž",
            [
                {"type": "Žvaigždė", "name": "Ąžuolas", "remark": "ąčęėįšųūž"},
            ],
            marks=pytest.mark.xfail(
                strict=True,
                reason="SQLite icontains folds ASCII only; MariaDB collation folds",
            ),
        ),
        pytest.param(
            "-c ąžuo",
            [
                {"type": "Žvaigždė", "name": "Ąžuolas", "remark": "ąčęėįšųūž"},
            ],
            marks=pytest.mark.xfail(
                strict=True,
                reason="SQLite icontains folds ASCII only; MariaDB collation folds",
            ),
        ),
        (
            "-r ąčęėįšųūž",
            [
                {"type": "Žvaigždė", "name": "Ąžuolas", "remark": "ąčęėįšųūž"},
            ],
        ),
    ],
)
def test_expense_search(main_user, _search, expect):
    ExpenseFactory(
        date=date(1999, 1, 1),
        expense_type=ExpenseTypeFactory(title="Type_A"),
        expense_name=ExpenseNameFactory(title="Name_A"),
        remark="XXX",
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        expense_type=ExpenseTypeFactory(title="Type_A"),
        expense_name=ExpenseNameFactory(title="Name_B"),
        remark="YYY",
    )
    ExpenseFactory(
        date=date(2000, 1, 1),
        expense_type=ExpenseTypeFactory(title="Type_B"),
        expense_name=ExpenseNameFactory(title="Name_A"),
        remark="ZZZ",
    )
    ExpenseFactory(
        date=date(2000, 2, 1),
        expense_type=ExpenseTypeFactory(title="Type_B"),
        expense_name=ExpenseNameFactory(title="Name_B"),
        remark="WWW",
    )
    ExpenseFactory(
        date=date(2001, 2, 1),
        expense_type=ExpenseTypeFactory(title="Žvaigždė"),
        expense_name=ExpenseNameFactory(title="Ąžuolas"),
        remark="ąčęėįšųūž",
    )

    q = search_expenses(main_user, _search)

    for row, expected in zip(q, expect, strict=True):
        assert row["expense_type__title"] == expected["type"]
        assert row["expense_name__title"] == expected["name"]
        assert row["remark"] == expected["remark"]


@pytest.mark.django_db
def test_search_totals():
    ExpenseFactory()
    ExpenseFactory()

    actual = search_totals(Expense.objects.all())

    assert actual == {
        "count": 2,
        "sum_price": 224,
        "sum_quantity": 26,
        "average": pytest.approx(224 / 26),
    }


@pytest.mark.django_db
def test_search_totals_zero_quantity_average_is_zero():
    ExpenseFactory(quantity=0)
    ExpenseFactory(quantity=0)

    actual = search_totals(Expense.objects.all())

    assert actual["sum_quantity"] == 0
    assert actual["average"] == 0
