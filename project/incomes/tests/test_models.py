from datetime import date

import factory
import pytest
from django.db import IntegrityError
from django.db.models.signals import post_save

from ...accounts.models import AccountBalance
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


# Income Type
def test_income_type_str():
    i = IncomeTypeFactory.build()

    assert str(i) == "Income Type"


@factory.django.mute_signals(post_save)
def test_income_type_items_journal(main_user, second_user):
    IncomeTypeFactory(title="T1")
    IncomeTypeFactory(title="T2", journal=second_user.journal)

    actual = IncomeTypeModelService(main_user).items()

    assert actual.count() == 1
    assert actual[0].title == "T1"


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


# Income
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


def test_sum_all_months_ordering(main_user, incomes):
    actual = list(IncomeModelService(main_user).sum_by_month(1999))

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[1]["date"] == date(1999, 2, 1)


def test_sum_one_month(main_user, incomes):
    expect = [{"date": date(1999, 1, 1), "sum": 550, "title": "incomes"}]

    actual = list(IncomeModelService(main_user).sum_by_month(1999, 1))

    assert expect == actual


@factory.django.mute_signals(post_save)
def test_incomes_items(main_user):
    IncomeFactory()

    assert len(IncomeModelService(main_user).items()) == 1


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
    qs = IncomeModelService(main_user).incomes()

    assert qs[0] == {"year": 1970, "incomes": 525, "category_id": 1}
    assert qs[1] == {"year": 1970, "incomes": 450, "category_id": 2}
    assert qs[2] == {"year": 1999, "incomes": 325, "category_id": 1}
    assert qs[3] == {"year": 1999, "incomes": 350, "category_id": 2}


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


def test_income_new_post_save(main_user):
    IncomeFactory()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 1000
    assert actual.balance == 1000


def test_income_update_post_save(main_user):
    obj = IncomeFactory(price=5)

    # update price
    obj_update = Income.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 1.0
    assert actual.balance == 1.0


def test_income_post_save_different_accounts():
    IncomeFactory(price=5, account=AccountFactory(title="X"))
    IncomeFactory(price=50, account=AccountFactory(title="Z"))

    actual = AccountBalance.objects.all()

    assert actual.count() == 4


def test_income_post_save_update_with_nothing_changed(main_user):
    obj = IncomeFactory(price=5)

    # update price
    obj_update = Income.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 5.0
    assert actual.balance == 5.0


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


def test_income_post_save_create_new_object_user_model_year(main_user):
    assert date(1999, 1, 1) == Journal.objects.get(pk=main_user.journal.pk).first_record

    IncomeFactory(date=date(1974, 2, 3), price=5)

    assert date(1974, 2, 3) == Journal.objects.get(pk=main_user.journal.pk).first_record


def test_income_post_save_update_object_user_model_year(main_user):
    assert date(1999, 1, 1) == Journal.objects.get(pk=main_user.journal.pk).first_record

    obj = IncomeFactory(price=5)

    income = Income.objects.get(pk=obj.pk)

    income.date = date(1974, 2, 3)
    income.save()

    assert date(1974, 2, 3) == Journal.objects.get(pk=main_user.journal.pk).first_record


def test_income_post_delete(main_user):
    obj = IncomeFactory()
    Income.objects.get(pk=obj.pk).delete()

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

    Income.objects.get(pk=obj.pk).delete()

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


def test_income_post_save_update_balance_row():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    obj = IncomeFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)

    assert actual.past == 5
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 6
    assert actual.delta == -6


def test_income_post_delete_new_signal():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    obj = IncomeFactory(date=date(1999, 1, 1), price=1)

    # check before delete
    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == 5
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 6
    assert actual.delta == -6

    Income.objects.get(pk=obj.pk).delete()

    assert not AccountBalance.objects.filter(
        account_id=obj.account.pk, year=1999
    ).exists()


def test_income_post_delete_empty_account_balance_table():
    obj_stay = IncomeFactory(date=date(1974, 1, 1), price=5)
    obj_del = IncomeFactory(date=date(1999, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    # delete Income object
    Income.objects.get(pk=obj_del.pk).delete()

    actual = AccountBalance.objects.all()

    assert actual.count() == 2
    assert actual[0].account_id == obj_stay.account.pk
    assert actual[0].year == 1974
    assert actual[0].past == 0
    assert actual[0].incomes == 5
    assert actual[0].expenses == 0
    assert actual[0].balance == 5
    assert actual[0].delta == -5


def test_income_years_sum(main_user):
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)

    actual = IncomeModelService(main_user).sum_by_year()

    assert actual[0]["year"] == 1998
    assert actual[0]["sum"] == 8.0

    assert actual[1]["year"] == 1999
    assert actual[1]["sum"] == 10.0


def test_income_year_sum_count_qs(main_user, django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        actual = [x["year"] for x in IncomeModelService(main_user).sum_by_year()]
        assert len(list(actual)) == 1


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
