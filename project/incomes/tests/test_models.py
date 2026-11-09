from datetime import date

import factory
import pytest
from django.db import IntegrityError
from django.db.models.signals import post_save

from ...accounts.models import Account, AccountBalance
from ...accounts.services.model_services import (
    AccountBalanceModelService,
)
from ...accounts.tests.factories import AccountFactory
from ...bookkeeping.tests.helper import quiet_build
from ...core.tests.utils import count_queries
from ...journals.models import Journal
from ..models import Income, IncomeType
from ..services.model_services import IncomeModelService, IncomeTypeModelService
from .factories import IncomeFactory, IncomeTypeFactory

pytestmark = pytest.mark.django_db


def test_income_type_str():
    i = IncomeTypeFactory.build()

    assert str(i) == "Income Type"


@factory.django.mute_signals(post_save)
def test_income_type_items_journal(main_user, second_user):
    IncomeTypeFactory(title="T1")
    IncomeTypeFactory(title="T2", journal=second_user.journal)

    actual = IncomeTypeModelService(main_user).items()

    assert [t.title for t in actual] == ["T1"]


def test_income_type_items_journal_queries(main_user, django_assert_max_num_queries):
    IncomeTypeFactory(title="T1")
    IncomeTypeFactory(title="T2")
    with django_assert_max_num_queries(1):
        [t.journal for t in IncomeTypeModelService(main_user).items()]


def test_income_type_unique_for_journal(main_user):
    IncomeType.objects.create(title="T", journal=main_user.journal)
    with pytest.raises(IntegrityError):
        IncomeType.objects.create(title="T", journal=main_user.journal)


def test_income_type_unique_for_journals(main_user, second_user):
    IncomeType.objects.create(title="T", journal=main_user.journal)
    IncomeType.objects.create(title="T", journal=second_user.journal)


def test_income_type_slug_unique_per_journal():
    obj1 = IncomeTypeFactory(title="Būstas")

    with pytest.raises(IntegrityError):
        IncomeTypeFactory(title="Bustas", journal=obj1.journal)


def test_income_str():
    i = IncomeFactory.build()

    assert str(i) == "1999-01-01: Income Type"


def test_sum_all_months(main_user, incomes):
    expect = [
        {"date": date(1999, 1, 1), "sum": 550, "title": "incomes"},
        {"date": date(1999, 2, 1), "sum": 125, "title": "incomes"},
    ]

    actual = list(IncomeModelService(main_user).sum_by_month(1999))

    assert expect == actual


def test_sum_one_month(main_user, incomes):
    expect = [{"date": date(1999, 1, 1), "sum": 550, "title": "incomes"}]

    actual = list(IncomeModelService(main_user).sum_by_month(1999, 1))

    assert expect == actual


@factory.django.mute_signals(post_save)
def test_incomes_items(main_user, second_user):
    income = IncomeFactory()
    IncomeFactory(
        account=AccountFactory(journal=second_user.journal),
        income_type=IncomeTypeFactory(title="T2", journal=second_user.journal),
    )

    assert list(IncomeModelService(main_user).items()) == [income]


def test_incomes_items_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = IncomeModelService(main_user).items()
        list([x["date"] for x in qs])


def test_incomes_year_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = IncomeModelService(main_user).year(1999)
        list([x["date"] for x in qs])


def test_incomes_income_sum_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = IncomeModelService(main_user).sum_by_month(1999)
        list([x["date"] for x in qs])


def test_balance(main_user, incomes):
    a1 = Account.objects.get(title="Account1").pk
    a2 = Account.objects.get(title="Account2").pk

    actual = list(IncomeModelService(main_user).incomes())

    assert actual == [
        {"year": 1970, "incomes": 525, "category_id": a1},
        {"year": 1970, "incomes": 450, "category_id": a2},
        {"year": 1999, "incomes": 325, "category_id": a1},
        {"year": 1999, "incomes": 350, "category_id": a2},
    ]


@factory.django.mute_signals(post_save)
def test_income_month_type_sum(main_user):
    IncomeFactory(
        price=4, date=date(1999, 1, 2), income_type=IncomeTypeFactory(title="I-2")
    )
    IncomeFactory(
        price=3, date=date(1999, 1, 1), income_type=IncomeTypeFactory(title="I-2")
    )
    IncomeFactory(
        price=1, date=date(1974, 1, 1), income_type=IncomeTypeFactory(title="I-1")
    )
    IncomeFactory(
        price=2, date=date(1999, 1, 2), income_type=IncomeTypeFactory(title="I-1")
    )
    IncomeFactory(
        price=1, date=date(1999, 1, 1), income_type=IncomeTypeFactory(title="I-1")
    )

    expect = [
        {"date": date(1999, 1, 1), "title": "I-1", "sum": 3},
        {"date": date(1999, 1, 1), "title": "I-2", "sum": 7},
    ]
    actual = IncomeModelService(main_user).sum_by_month_and_type(1999)

    assert expect == [*actual]


@factory.django.mute_signals(post_save)
def test_income_year_type_sum(main_user):
    IncomeFactory(
        price=1, date=date(1974, 1, 1), income_type=IncomeTypeFactory(title="I-1")
    )
    IncomeFactory(
        price=2, date=date(1999, 1, 2), income_type=IncomeTypeFactory(title="I-1")
    )
    IncomeFactory(
        price=1, date=date(1999, 1, 1), income_type=IncomeTypeFactory(title="I-1")
    )
    IncomeFactory(
        price=3, date=date(1999, 1, 2), income_type=IncomeTypeFactory(title="I-2")
    )
    IncomeFactory(
        price=4, date=date(1999, 1, 1), income_type=IncomeTypeFactory(title="I-2")
    )

    expect = [
        {"date": date(1974, 1, 1), "title": "I-1", "sum": 1},
        {"date": date(1999, 1, 1), "title": "I-1", "sum": 3},
        {"date": date(1999, 1, 1), "title": "I-2", "sum": 7},
    ]
    actual = IncomeModelService(main_user).sum_by_year_and_type()

    assert expect == [*actual]


def _created(income):
    pass


def _price_changed(income):
    income.price = 1
    income.save()


def _saved_unchanged(income):
    income.save()


@pytest.mark.parametrize(
    "save, expected",
    [(_created, 5), (_price_changed, 1), (_saved_unchanged, 5)],
    ids=["new", "update", "nothing_changed"],
)
def test_income_save_syncs_its_balance_row(main_user, save, expected):
    save(IncomeFactory(price=5))

    actual = [
        (row.account.title, row.incomes, row.balance)
        for row in AccountBalanceModelService(main_user).year(1999)
    ]

    assert actual == [("Account1", expected, expected)]


def test_income_post_save_different_accounts():
    IncomeFactory(price=5, account=AccountFactory(title="X"))
    IncomeFactory(price=50, account=AccountFactory(title="Z"))

    actual = [
        (row.account.title, row.year, row.incomes)
        for row in AccountBalance.objects.order_by("account__title", "year")
    ]

    assert actual == [("X", 1999, 5), ("X", 2000, 0), ("Z", 1999, 50), ("Z", 2000, 0)]


def test_income_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title="XXX")

    obj = IncomeFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 5.0
    assert actual.balance == 5.0

    obj.account = account_new
    obj.save()

    assert not AccountBalance.objects.filter(account_id=account_old.pk).exists()

    actual = AccountBalance.objects.get(account_id=account_new.pk, year=1999)
    assert actual.account.title == "XXX"
    assert actual.incomes == 5.0
    assert actual.balance == 5.0


def _created_in_1974():
    IncomeFactory(date=date(1974, 2, 3))


def _moved_to_1974():
    income = IncomeFactory()
    income.date = date(1974, 2, 3)
    income.save()


@pytest.mark.parametrize(
    "save", [_created_in_1974, _moved_to_1974], ids=["new", "update"]
)
def test_income_save_lowers_the_first_record(main_user, save):
    assert Journal.objects.get(pk=main_user.journal.pk).first_record == date(1999, 1, 1)

    save()

    assert Journal.objects.get(pk=main_user.journal.pk).first_record == date(1974, 2, 3)


def test_income_post_delete(main_user):
    IncomeFactory().delete()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 0
    assert Income.objects.all().count() == 0


def test_income_post_delete_with_update():
    IncomeFactory(price=1)

    obj = IncomeFactory(price=5)
    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 6.0
    assert actual.balance == 6.0

    obj.delete()

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 1.0
    assert actual.balance == 1.0

    assert Income.objects.all().count() == 1


def _new_income(income):
    Income.objects.create(
        date=income.date,
        price=2,
        account=income.account,
        income_type=income.income_type,
    )


def _new_income_into_no_balances(income):
    AccountBalance.objects.all().delete()
    _new_income(income)


def _changed_income(income):
    income.price += 1
    income.save()


@pytest.mark.parametrize(
    "save",
    [_new_income, _new_income_into_no_balances, _changed_income],
    ids=["new", "new_into_no_balances", "update"],
)
def test_an_income_save_costs_as_many_queries_with_2_years_as_with_6(main_user, save):
    with quiet_build(main_user):
        first = IncomeFactory(date=date(1990, 1, 1))
        IncomeFactory(date=date(1991, 1, 1))
    two = count_queries(lambda: save(first))

    with quiet_build(main_user):
        for year in range(1992, 1996):
            IncomeFactory(date=date(year, 1, 1))
    six = count_queries(lambda: save(first))

    assert six == two


def test_income_post_save_first_year_record():
    obj1 = IncomeFactory(date=date(1974, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    obj2 = IncomeFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj2.account.pk, year=1999)
    assert actual.past == 5
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 6
    assert actual.delta == -6

    actual = AccountBalance.objects.get(account_id=obj1.account.pk, year=1974)
    assert actual.past == 0
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5
    assert actual.delta == -5


def test_income_post_delete_new_signal():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    obj = IncomeFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == 5
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 6
    assert actual.delta == -6

    obj.delete()

    assert not AccountBalance.objects.filter(
        account_id=obj.account.pk, year=1999
    ).exists()


def test_income_post_delete_empty_account_balance_table():
    obj_stay = IncomeFactory(date=date(1974, 1, 1), price=5)
    obj_del = IncomeFactory(date=date(1999, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    obj_del.delete()

    actual = [
        (row.year, row.past, row.incomes, row.expenses, row.balance, row.delta)
        for row in AccountBalance.objects.filter(account=obj_stay.account)
    ]
    others = AccountBalance.objects.exclude(account=obj_stay.account)

    assert actual == [(1974, 0, 5, 0, 5, -5), (1975, 5, 0, 0, 5, -5)]
    assert not others.exists()


def test_income_years_sum(main_user):
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)

    actual = list(IncomeModelService(main_user).sum_by_year())

    assert actual == [{"year": 1998, "sum": 8.0}, {"year": 1999, "sum": 10.0}]


def test_income_year_sum_count_qs(main_user, django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        actual = [x["year"] for x in IncomeModelService(main_user).sum_by_year()]

    assert actual == [1999]


@pytest.mark.parametrize(
    "types, expected",
    [(["x"], 10.0), (["x", "y"], 25.0)],
    ids=["one_type", "two_types"],
)
def test_income_year_sum_filter(main_user, types, expected):
    IncomeFactory(
        date=date(1999, 1, 1),
        price=5.0,
        income_type=IncomeTypeFactory(title="1", type="x"),
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=5.0,
        income_type=IncomeTypeFactory(title="2", type="x"),
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=15.0,
        income_type=IncomeTypeFactory(title="3", type="y"),
    )
    IncomeFactory(
        date=date(1999, 1, 1),
        price=20.0,
        income_type=IncomeTypeFactory(title="4", type="z"),
    )

    actual = list(IncomeModelService(main_user).sum_by_year(types))

    assert actual == [{"year": 1999, "sum": expected}]


def test_income_year_sum_filter_count_qs(main_user, django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        list([x["year"] for x in IncomeModelService(main_user).sum_by_year(["x"])])


def test_income_journal_is_its_accounts(second_user):
    journal = second_user.journal

    obj = IncomeFactory.build(account=AccountFactory(journal=journal))

    assert obj.journal == journal
