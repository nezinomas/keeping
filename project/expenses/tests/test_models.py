from datetime import date

import factory
import mock
import pytest
import time_machine
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import IntegrityError, models, transaction
from django.db.models.signals import post_save
from override_storage import override_storage

from ...accounts.models import Account, AccountBalance
from ...accounts.services.model_services import AccountBalanceModelService
from ...accounts.tests.factories import AccountFactory
from ...journals.models import Journal
from ..models import Expense, ExpenseKeyword, ExpenseName, ExpenseType
from ..services.model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
    ExpenseTypeModelService,
)
from .factories import (
    ExpenseFactory,
    ExpenseKeywordFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)

pytestmark = pytest.mark.django_db
is_sqlite = "sqlite3" in settings.DATABASES["default"]["ENGINE"]


def test_expense_type_str():
    expense_type = ExpenseTypeFactory.build()

    assert str(expense_type) == "Expense Type"


@factory.django.mute_signals(post_save)
def test_month_expense_type(main_user, expenses):
    expect = [
        {"date": date(1999, 1, 1), "sum": 50, "title": "Expense Type"},
        {"date": date(1999, 12, 1), "sum": 125, "title": "Expense Type"},
    ]

    actual = [*ExpenseModelService(main_user).sum_by_month_and_type(1999)]

    assert actual == expect


def test_day_expense_type(main_user, expenses_january):
    expect = [
        {
            "date": date(1999, 1, 1),
            "sum": 50,
            "title": "Expense Type",
            "exception_sum": 25,
        },
        {
            "date": date(1999, 1, 11),
            "sum": 50,
            "title": "Expense Type",
            "exception_sum": 0,
        },
    ]

    actual = [*ExpenseModelService(main_user).sum_by_day_and_type(1999, 1)]

    assert actual == expect


def test_expense_type_items(main_user):
    ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2")

    actual = ExpenseTypeModelService(main_user).items()

    assert actual.count() == 2


def test_expense_type_items_user(main_user, second_user):
    ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2", journal=second_user.journal)

    actual = ExpenseTypeModelService(main_user).items()

    assert actual.count() == 1


def test_expense_type_related_qs_count(main_user, django_assert_max_num_queries):
    ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2")
    ExpenseTypeFactory(title="T3")

    with django_assert_max_num_queries(2):
        list(item.title for item in ExpenseTypeModelService(main_user).items())


def test_post_save_expense_type_insert_new(main_user):
    obj = ExpenseType(title="e1", journal=main_user.journal)
    obj.save()

    actual = AccountBalanceModelService(main_user).items()

    assert actual.count() == 0


def test_expense_type_unique_users(main_user, second_user):
    ExpenseType.objects.create(title="T1", journal=main_user.journal)
    ExpenseType.objects.create(title="T1", journal=second_user.journal)

    assert ExpenseType.objects.filter(title="T1").count() == 2


def test_expense_type_slug_unique_per_journal():
    obj1 = ExpenseTypeFactory(title="Būstas")

    with pytest.raises(IntegrityError):
        ExpenseTypeFactory(title="Bustas", journal=obj1.journal)


def test_expense_name_str():
    expense_name = ExpenseNameFactory.build()

    assert str(expense_name) == "Expense Name"


def test_expense_name_items(main_user):
    ExpenseNameFactory(title="N1")
    ExpenseNameFactory(title="N2")

    actual = ExpenseNameModelService(main_user).items()

    assert actual.count() == 2


def test_expense_name_related_different_users(main_user, second_user):
    main_type = ExpenseTypeFactory(title="T1")
    second_type = ExpenseTypeFactory(title="T2", journal=second_user.journal)

    ExpenseNameFactory(title="N1", parent=main_type)
    ExpenseNameFactory(title="N2", parent=second_type)

    actual = ExpenseNameModelService(main_user).items()

    assert len(actual) == 1
    assert actual[0].title == "N1"


def test_expense_name_related_qs_count(main_user, django_assert_max_num_queries):
    ExpenseNameFactory(title="T1")
    ExpenseNameFactory(title="T2")

    with django_assert_max_num_queries(1):
        list(item.parent.title for item in ExpenseNameModelService(main_user).items())


def test_expense_name_year(main_user):
    ExpenseNameFactory(title="N1", valid_for=2000)
    ExpenseNameFactory(title="N2", valid_for=1999)

    actual = ExpenseNameModelService(main_user).year(2000)

    assert actual.count() == 1
    assert actual[0].title == "N1"


def test_expense_name_year_lists_unlimited_names_before_the_years(main_user):
    ExpenseNameFactory(title="N1", valid_for=2000)
    ExpenseNameFactory(title="N2")

    actual = ExpenseNameModelService(main_user).year(2000)

    assert actual.count() == 2
    assert actual[0].title == "N2"
    assert actual[1].title == "N1"


def test_expense_name_no_duplicates():
    parent = ExpenseTypeFactory(title="P1")
    ExpenseName(title="N1", parent=parent).save()

    with pytest.raises(IntegrityError):
        ExpenseName(title="N1", parent=parent).save()


def test_expense_name_slug_unique_per_parent():
    obj1 = ExpenseNameFactory(title="Būstas")

    with pytest.raises(IntegrityError):
        ExpenseNameFactory(title="Bustas", parent=obj1.parent)


def test_expense_name_longest_title_is_valid_with_its_slug():
    obj = ExpenseNameFactory(title="a" * 254)

    obj.full_clean()


def test_expense_name_slug_as_long_as_title():
    title = ExpenseName._meta.get_field("title")
    slug = ExpenseName._meta.get_field("slug")

    assert slug.max_length == title.max_length


def test_expense_str():
    expense = ExpenseFactory.build()

    assert str(expense) == "1999-01-01/Expense Type/Expense Name"


def test_expense_fields_types():
    assert isinstance(Expense._meta.get_field("date"), models.DateField)
    assert isinstance(Expense._meta.get_field("price"), models.PositiveIntegerField)
    assert isinstance(Expense._meta.get_field("quantity"), models.IntegerField)
    assert isinstance(Expense._meta.get_field("expense_type"), models.ForeignKey)
    assert isinstance(Expense._meta.get_field("expense_name"), models.ForeignKey)
    assert isinstance(Expense._meta.get_field("remark"), models.TextField)
    assert isinstance(Expense._meta.get_field("exception"), models.BooleanField)
    assert isinstance(Expense._meta.get_field("account"), models.ForeignKey)
    assert isinstance(Expense._meta.get_field("attachment"), models.FileField)


@override_storage()
@time_machine.travel("1974-1-1")
def test_expense_attachment_field(main_user):
    file_mock = mock.MagicMock(spec=File, name="FileMock")
    file_mock.name = "test1.jpg"

    expense = ExpenseFactory(attachment=file_mock)
    pk = str(main_user.journal.pk)

    assert str(expense.attachment) == f"{pk}/expense-type/1974.01_test1.jpg"


@factory.django.mute_signals(post_save)
def test_expense_related(main_user, second_user):
    main_account = AccountFactory(title="A1")
    second_account = AccountFactory(title="A2", journal=second_user.journal)
    main_type = ExpenseTypeFactory(title="T1")
    second_type = ExpenseTypeFactory(title="T2", journal=second_user.journal)

    ExpenseFactory(expense_type=main_type, account=main_account)
    ExpenseFactory(expense_type=second_type, account=second_account)

    actual = ExpenseModelService(main_user).items()

    assert len(actual) == 1
    assert str(actual[0].expense_type) == "T1"


@factory.django.mute_signals(post_save)
def test_expense_year(main_user):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = ExpenseModelService(main_user).year(2000)

    assert actual.count() == 1


def test_expense_year_query_count(main_user, django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        [item.expense_type for item in ExpenseModelService(main_user).year(2000)]


@factory.django.mute_signals(post_save)
def test_expense_items(main_user):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = ExpenseModelService(main_user).items()

    assert actual.count() == 2


def test_expense_items_query_count(main_user, django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        [item.expense_type.title for item in ExpenseModelService(main_user).items()]


@factory.django.mute_signals(post_save)
def test_month_name_sum(main_user):
    ExpenseFactory(
        date=date(1974, 1, 1),
        price=1,
        expense_type=ExpenseTypeFactory(title="T1"),
        expense_name=ExpenseNameFactory(title="N1"),
    )
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=2,
        expense_type=ExpenseTypeFactory(title="T1"),
        expense_name=ExpenseNameFactory(title="N1"),
    )
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=3,
        expense_type=ExpenseTypeFactory(title="T2"),
        expense_name=ExpenseNameFactory(title="N1"),
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        price=4,
        expense_type=ExpenseTypeFactory(title="T1"),
        expense_name=ExpenseNameFactory(title="N1"),
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        price=5,
        expense_type=ExpenseTypeFactory(title="T1"),
        expense_name=ExpenseNameFactory(title="N1"),
    )

    expect = [
        {
            "date": date(1999, 1, 1),
            "title": "N1",
            "type_title": "T1",
            "type_slug": "t1",
            "sum": 2,
        },
        {
            "date": date(1999, 1, 1),
            "title": "N1",
            "type_title": "T2",
            "type_slug": "t2",
            "sum": 3,
        },
        {
            "date": date(1999, 2, 1),
            "title": "N1",
            "type_title": "T1",
            "type_slug": "t1",
            "sum": 9,
        },
    ]

    actual = ExpenseModelService(main_user).sum_by_month_and_name(1999)

    assert [*actual] == expect


@factory.django.mute_signals(post_save)
@time_machine.travel("1999-06-01")
def test_expense_last_months(main_user):
    ExpenseFactory(date=date(1998, 11, 30), price=3)
    ExpenseFactory(date=date(1998, 12, 31), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=7)

    actual = ExpenseModelService(main_user).last_months(6)

    assert actual[0]["sum"] == 11
    assert actual[0]["title"] == "Expense Type"


@time_machine.travel("1999-06-01")
@factory.django.mute_signals(post_save)
def test_expense_last_months_empty_expenses(main_user):
    ExpenseTypeFactory()

    actual = ExpenseModelService(main_user).last_months(6)
    assert not actual


@time_machine.travel("1999-06-01")
@factory.django.mute_signals(post_save)
def test_expense_last_months_one_of_expenses_empty(main_user):
    used_type = ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2")

    ExpenseFactory(date=date(1999, 1, 1), price=3, expense_type=used_type)

    actual = ExpenseModelService(main_user).last_months(6)

    assert len(actual) == 1
    assert actual[0]["sum"] == 3
    assert actual[0]["title"] == "T1"


@factory.django.mute_signals(post_save)
@time_machine.travel("1999-06-01")
def test_expense_last_months_qs_count(main_user, django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1), price=2)

    with django_assert_max_num_queries(1):
        list(ExpenseModelService(main_user).last_months())


@factory.django.mute_signals(post_save)
def test_expense_years_sum(main_user):
    ExpenseFactory(date=date(1998, 1, 1), price=4)
    ExpenseFactory(date=date(1998, 1, 1), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=5)
    ExpenseFactory(date=date(1999, 1, 1), price=5)

    actual = ExpenseModelService(main_user).sum_by_year()

    assert actual[0]["year"] == 1998
    assert actual[0]["sum"] == 8

    assert actual[1]["year"] == 1999
    assert actual[1]["sum"] == 10


@factory.django.mute_signals(post_save)
def test_expense_sum_by_month(main_user):
    ExpenseFactory(date=date(1999, 2, 3), price=2)
    ExpenseFactory(date=date(1999, 2, 12), price=4)
    ExpenseFactory(date=date(1999, 1, 31), price=2)
    ExpenseFactory(date=date(1999, 1, 13), price=1)

    actual = ExpenseModelService(main_user).sum_by_month(1999)

    assert list(actual) == [
        {"sum": 3, "date": date(1999, 1, 1), "title": "expenses"},
        {"sum": 6, "date": date(1999, 2, 1), "title": "expenses"},
    ]


def test_expense_updates_journal_first_record():
    assert Journal.objects.first().first_record == date(1999, 1, 1)

    ExpenseFactory(date=date(1974, 2, 2))

    assert Journal.objects.first().first_record == date(1974, 2, 2)


def test_expense_new_post_save(main_user):
    ExpenseFactory(price=1)

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    balance = actual[0]

    assert balance.account.title == "Account1"
    assert balance.expenses == 1
    assert balance.balance == -1


def test_expense_update_post_save(main_user):
    obj = Expense.objects.create(
        date=date(1999, 1, 1),
        price=112,
        quantity=1,
        account=AccountFactory(),
        expense_type=ExpenseTypeFactory(),
        expense_name=ExpenseNameFactory(),
    )

    obj_update = Expense.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    balance = actual[0]

    assert balance.account.title == "Account1"
    assert balance.expenses == 1
    assert balance.balance == -1


def test_expense_post_save_update_with_nothing_changed(main_user):
    obj = ExpenseFactory(price=5)

    obj_update = Expense.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    balance = actual[0]

    assert balance.account.title == "Account1"
    assert balance.incomes == 0
    assert balance.expenses == 5
    assert balance.balance == -5


def test_expense_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title="XXX")

    obj = ExpenseFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5

    obj_new = Expense.objects.get(pk=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    with pytest.raises(AccountBalance.DoesNotExist):
        AccountBalance.objects.get(account_id=account_old.pk, year=1999)

    actual = AccountBalance.objects.get(account_id=account_new.pk, year=1999)
    assert actual.account.title == "XXX"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5


def test_expense_post_save_update_object_user_model_year(main_user):
    assert date(1999, 1, 1) == Journal.objects.get(pk=main_user.journal.pk).first_record

    obj = ExpenseFactory(price=5)

    instance = Expense.objects.get(pk=obj.pk)

    instance.date = date(1974, 2, 3)
    instance.save()

    assert date(1974, 2, 3) == Journal.objects.get(pk=main_user.journal.pk).first_record


def test_expense_post_delete(main_user):
    ExpenseFactory()

    Expense.objects.first().delete()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 0
    assert Expense.objects.all().count() == 0


def test_expense_post_delete_with_update():
    ExpenseFactory(date=date(1974, 1, 1), price=5)
    obj = ExpenseFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == -5
    assert actual.incomes == 0
    assert actual.expenses == 1
    assert actual.balance == -6
    assert actual.delta == 6

    Expense.objects.get(pk=obj.pk).delete()

    with pytest.raises(AccountBalance.DoesNotExist):
        AccountBalance.objects.get(account_id=obj.account.pk, year=1999)


def test_expense_post_save_first_year_record():
    obj1 = ExpenseFactory(date=date(1974, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    obj2 = ExpenseFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj2.account.pk, year=1999)
    assert actual.past == -5
    assert actual.incomes == 0
    assert actual.expenses == 1
    assert actual.balance == -6
    assert actual.delta == 6

    actual = AccountBalance.objects.get(account_id=obj1.account.pk, year=1974)
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5
    assert actual.delta == 5


def test_expense_post_delete_empty_account_balance_table():
    obj_stay = ExpenseFactory(date=date(1974, 1, 1), price=5)
    obj_del = ExpenseFactory(date=date(1999, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    Expense.objects.get(pk=obj_del.pk).delete()

    actual = AccountBalance.objects.all()

    assert actual.count() == 2
    assert actual[0].account_id == obj_stay.account.pk
    assert actual[0].year == 1974
    assert actual[0].past == 0
    assert actual[0].incomes == 0
    assert actual[0].expenses == 5
    assert actual[0].balance == -5
    assert actual[0].delta == 5


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "sum_by, title",
    [
        pytest.param(ExpenseModelService.sum_by_year_type, "Expense Type", id="type"),
        pytest.param(
            ExpenseModelService.sum_by_year_name,
            "Expense Type / Expense Name",
            id="name",
        ),
    ],
)
def test_expense_sum_by_year(main_user, sum_by, title):
    ExpenseFactory(date=date(1111, 1, 1), price=1)
    ExpenseFactory(date=date(1999, 1, 1), price=2)
    ExpenseFactory(date=date(1111, 1, 1), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=10)

    actual = sum_by(ExpenseModelService(main_user))

    assert actual[0]["year"] == 1111
    assert actual[0]["title"] == title
    assert actual[0]["sum"] == 5
    assert actual[1]["year"] == 1999
    assert actual[1]["title"] == title
    assert actual[1]["sum"] == 12


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "sum_by, factory_class, expense_kwargs, filter_kwargs, title",
    [
        pytest.param(
            ExpenseModelService.sum_by_year_type,
            ExpenseTypeFactory,
            lambda obj: {"expense_type": obj},
            lambda obj: {"expense_type": [obj.pk]},
            "X",
            id="type",
        ),
        pytest.param(
            ExpenseModelService.sum_by_year_name,
            ExpenseNameFactory,
            lambda obj: {"expense_name": obj},
            lambda obj: {"expense_name": [obj.pk]},
            "Expense Type / X",
            id="name",
        ),
    ],
)
def test_expense_sum_by_year_filtering(
    main_user, sum_by, factory_class, expense_kwargs, filter_kwargs, title
):
    picked = factory_class(title="X")
    other = factory_class(title="Y")

    ExpenseFactory(**expense_kwargs(picked), date=date(1111, 1, 1), price=1)
    ExpenseFactory(**expense_kwargs(picked), date=date(1999, 1, 1), price=2)
    ExpenseFactory(**expense_kwargs(picked), date=date(1111, 1, 1), price=4)
    ExpenseFactory(**expense_kwargs(picked), date=date(1999, 1, 1), price=10)

    ExpenseFactory(**expense_kwargs(other), date=date(1111, 1, 1), price=1)
    ExpenseFactory(**expense_kwargs(other), date=date(1999, 1, 1), price=2)
    ExpenseFactory(**expense_kwargs(other), date=date(1111, 1, 1), price=4)
    ExpenseFactory(**expense_kwargs(other), date=date(1999, 1, 1), price=10)

    actual = sum_by(ExpenseModelService(main_user), **filter_kwargs(picked))

    assert actual[0]["year"] == 1111
    assert actual[0]["title"] == title
    assert actual[0]["sum"] == 5
    assert actual[1]["year"] == 1999
    assert actual[1]["title"] == title
    assert actual[1]["sum"] == 12


@factory.django.mute_signals(post_save)
def test_expenses(main_user, expenses):
    account1 = Account.objects.get(title="Account1")
    account2 = Account.objects.get(title="Account2")

    actual = ExpenseModelService(main_user).expenses()

    assert actual[0]["year"] == 1970
    assert actual[0]["category_id"] == account1.pk
    assert actual[0]["expenses"] == 250

    assert actual[1]["year"] == 1970
    assert actual[1]["category_id"] == account2.pk
    assert actual[1]["expenses"] == 225

    assert actual[2]["year"] == 1999
    assert actual[2]["category_id"] == account1.pk
    assert actual[2]["expenses"] == 50

    assert actual[3]["year"] == 1999
    assert actual[3]["category_id"] == account2.pk
    assert actual[3]["expenses"] == 125


@factory.django.mute_signals(post_save)
def test_sum_by_day_and_type_basic_grouping(main_user):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")

    ExpenseFactory(date=date(1999, 1, 1), price=10, expense_type=t1)
    ExpenseFactory(date=date(1999, 1, 1), price=20, expense_type=t1)
    ExpenseFactory(date=date(1999, 1, 1), price=50, expense_type=t2)
    ExpenseFactory(date=date(1999, 1, 2), price=100, expense_type=t1)

    actual = list(ExpenseModelService(main_user).sum_by_day_and_type(1999, 1))

    assert len(actual) == 3

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[0]["title"] == "T1"
    assert actual[0]["sum"] == 30
    assert actual[0]["exception_sum"] == 0

    assert actual[1]["date"] == date(1999, 1, 1)
    assert actual[1]["title"] == "T2"
    assert actual[1]["sum"] == 50
    assert actual[1]["exception_sum"] == 0

    assert actual[2]["date"] == date(1999, 1, 2)
    assert actual[2]["title"] == "T1"
    assert actual[2]["sum"] == 100
    assert actual[2]["exception_sum"] == 0


@factory.django.mute_signals(post_save)
def test_sum_by_day_and_type_calculates_exceptions(main_user):
    t1 = ExpenseTypeFactory(title="T1")

    ExpenseFactory(date=date(1999, 1, 1), price=15, expense_type=t1, exception=1)
    ExpenseFactory(date=date(1999, 1, 1), price=25, expense_type=t1, exception=0)

    actual = list(ExpenseModelService(main_user).sum_by_day_and_type(1999, 1))

    assert len(actual) == 1
    assert actual[0]["sum"] == 40
    assert actual[0]["exception_sum"] == 15


@factory.django.mute_signals(post_save)
def test_sum_by_day_and_type_ignores_other_dates(main_user):
    t1 = ExpenseTypeFactory(title="T1")

    ExpenseFactory(date=date(1999, 1, 15), price=10, expense_type=t1)
    ExpenseFactory(date=date(1999, 2, 15), price=20, expense_type=t1)
    ExpenseFactory(date=date(1998, 1, 15), price=30, expense_type=t1)

    actual = list(ExpenseModelService(main_user).sum_by_day_and_type(1999, 1))

    assert len(actual) == 1
    assert actual[0]["date"] == date(1999, 1, 15)
    assert actual[0]["sum"] == 10


@pytest.mark.skipif(
    is_sqlite, reason="SQLite does not support MariaDB's FORMAT() function."
)
@pytest.mark.parametrize(
    "lang, expected",
    [
        pytest.param("lt", "12,50", id="lt"),
        pytest.param("en", "12.50", id="en"),
    ],
)
def test_expenses_list_dynamic_locale(main_user, lang, expected):
    main_user.journal.lang = lang
    main_user.journal.save()

    ExpenseFactory(price=1250)

    qs = ExpenseModelService(main_user).items()
    actual = list(ExpenseModelService(main_user).expenses_list(qs))

    assert len(actual) == 1
    assert actual[0]["price_str"] == expected


def test_expense_keyword_str():
    keyword = ExpenseKeywordFactory.build(keyword="jogurt")

    assert str(keyword) == "jogurt"


def test_expense_keyword_normalises_on_save(main_user):
    obj = ExpenseKeywordFactory(journal=main_user.journal, keyword="  Jogurt ")

    obj.refresh_from_db()

    assert obj.keyword == "jogurt"


def test_expense_keyword_unique_per_journal(main_user):
    ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt")

    with pytest.raises(IntegrityError), transaction.atomic():
        ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt")


def test_expense_keyword_same_keyword_different_journal(main_user, second_user):
    other_name = ExpenseNameFactory(
        parent=ExpenseTypeFactory(title="Buitinės", journal=second_user.journal)
    )
    ExpenseKeywordFactory(journal=main_user.journal, keyword="jogurt")
    ExpenseKeywordFactory(
        journal=second_user.journal, keyword="jogurt", expense_name=other_name
    )

    assert ExpenseKeyword.objects.count() == 2


def test_expense_keyword_clean_passes_for_own_journal_name(main_user):
    name = ExpenseNameFactory(parent=ExpenseTypeFactory(journal=main_user.journal))
    obj = ExpenseKeywordFactory.build(journal=main_user.journal, expense_name=name)

    obj.clean()


def test_expense_keyword_clean_fails_for_other_journal_name(main_user, second_user):
    name = ExpenseNameFactory(parent=ExpenseTypeFactory(journal=second_user.journal))
    obj = ExpenseKeywordFactory.build(journal=main_user.journal, expense_name=name)

    with pytest.raises(ValidationError):
        obj.clean()


def test_expense_keyword_keeps_its_name_among_same_titled_names(main_user):
    maistas = ExpenseTypeFactory(title="Maistas", journal=main_user.journal)
    buitines = ExpenseTypeFactory(title="Buitinės", journal=main_user.journal)
    ExpenseNameFactory(title="Kita", parent=maistas)
    kita = ExpenseNameFactory(title="Kita", parent=buitines)

    obj = ExpenseKeywordFactory(
        journal=main_user.journal, keyword="servet", expense_name=kita
    )
    obj.refresh_from_db()

    assert obj.expense_name == kita
    assert obj.expense_name.parent == buitines


def test_expense_keyword_clean_fails_for_same_titled_name_of_other_journal(
    main_user, second_user
):
    own_type = ExpenseTypeFactory(title="Maistas", journal=main_user.journal)
    other_type = ExpenseTypeFactory(title="Buitinės", journal=second_user.journal)
    ExpenseNameFactory(title="Kita", parent=own_type)
    other = ExpenseNameFactory(title="Kita", parent=other_type)
    obj = ExpenseKeywordFactory.build(journal=main_user.journal, expense_name=other)

    with pytest.raises(ValidationError):
        obj.clean()


def test_expense_keyword_clean_other_journal_name_message(main_user, second_user):
    name = ExpenseNameFactory(parent=ExpenseTypeFactory(journal=second_user.journal))
    obj = ExpenseKeywordFactory.build(journal=main_user.journal, expense_name=name)

    with pytest.raises(ValidationError) as error:
        obj.clean()

    assert error.value.message_dict == {
        "expense_name": ["Išlaidų pavadinimas priklauso kitam žurnalui."]
    }


def test_expense_keyword_full_clean_without_name_is_a_field_error(main_user):
    obj = ExpenseKeyword(journal=main_user.journal, keyword="jogurt")

    with pytest.raises(ValidationError) as error:
        obj.full_clean()

    assert "expense_name" in error.value.message_dict


def test_expense_keyword_full_clean_refuses_other_spelling_of_existing(main_user):
    name = ExpenseNameFactory(parent=ExpenseTypeFactory(journal=main_user.journal))
    ExpenseKeywordFactory(
        journal=main_user.journal, keyword="jogurt", expense_name=name
    )
    obj = ExpenseKeyword(journal=main_user.journal, keyword="Jogurt", expense_name=name)

    with pytest.raises(ValidationError):
        obj.full_clean()


@pytest.mark.parametrize("keyword", [" ab ", "   "])
def test_expense_keyword_full_clean_checks_length_after_normalising(main_user, keyword):
    name = ExpenseNameFactory(parent=ExpenseTypeFactory(journal=main_user.journal))
    obj = ExpenseKeyword(journal=main_user.journal, keyword=keyword, expense_name=name)

    with pytest.raises(ValidationError) as error:
        obj.full_clean()

    assert "keyword" in error.value.message_dict


def test_expense_journal_is_its_types(second_user):
    journal = second_user.journal

    obj = ExpenseFactory.build(expense_type=ExpenseTypeFactory(journal=journal))

    assert obj.journal == journal
