from datetime import date

import factory
import pytest
from django.db.models.signals import post_save

from ...services.search import search_incomes
from ..factories import IncomeFactory, IncomeTypeFactory

FOUND = ["Income Type"]


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "_search, income_types",
    [
        ("1999", FOUND),
        ("-y 1999", FOUND),
        ("1999.1", FOUND),
        ("1999-1", FOUND),
        ("-y 1999 -m 1", FOUND),
        ("2000", []),
        ("-y 2000", []),
        ("a", []),
        ("ab", []),
        ("type", FOUND),
        ("-c type", FOUND),
        ("remark", FOUND),
        ("-r remark", FOUND),
        ("1999.1 type", FOUND),
        ("1999-1 type", FOUND),
        ("-y 1999 -m 1 -c type", FOUND),
    ],
)
def test_incomes_search(main_user, _search, income_types):
    IncomeFactory()
    IncomeFactory(
        date=date(3333, 1, 1), income_type=IncomeTypeFactory(title="Y"), remark="ZZZ"
    )

    actual = [
        (row["date"], row["income_type__title"])
        for row in search_incomes(main_user, _search)
    ]

    assert actual == [(date(1999, 1, 1), title) for title in income_types]


@pytest.mark.django_db
@factory.django.mute_signals(post_save)
def test_incomes_search_orders_newest_first(main_user):
    IncomeFactory(date=date(1000, 1, 1))
    IncomeFactory()

    actual = [row["date"] for row in search_incomes(main_user, "remark")]

    assert actual == [date(1999, 1, 1), date(1000, 1, 1)]
