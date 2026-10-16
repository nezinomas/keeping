from datetime import date

import factory
import pytest
import time_machine
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
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

TODAY = date(1999, 6, 1)


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


@pytest.mark.parametrize(
    "t2_owner, expect",
    [
        pytest.param("main", ["T1", "T2"], id="same_journal"),
        pytest.param("second", ["T1"], id="other_journal"),
    ],
)
def test_expense_type_items(main_user, second_user, t2_owner, expect):
    owners = {"main": main_user, "second": second_user}
    ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2", journal=owners[t2_owner].journal)

    actual = ExpenseTypeModelService(main_user).items()

    assert [a.title for a in actual] == expect


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


@pytest.mark.parametrize(
    "n2_owner, expect",
    [
        pytest.param("main", ["N1", "N2"], id="same_journal"),
        pytest.param("second", ["N1"], id="other_journal"),
    ],
)
def test_expense_name_items(main_user, second_user, n2_owner, expect):
    owners = {"main": main_user, "second": second_user}
    ExpenseNameFactory(title="N1", parent=ExpenseTypeFactory(title="T1"))
    ExpenseNameFactory(
        title="N2",
        parent=ExpenseTypeFactory(title="T2", journal=owners[n2_owner].journal),
    )

    actual = ExpenseNameModelService(main_user).items()

    assert [a.title for a in actual] == expect


def test_expense_name_related_qs_count(main_user, django_assert_max_num_queries):
    ExpenseNameFactory(title="T1")
    ExpenseNameFactory(title="T2")

    with django_assert_max_num_queries(1):
        list(item.parent.title for item in ExpenseNameModelService(main_user).items())


@pytest.mark.parametrize(
    "second_valid_for, expect",
    [
        pytest.param(1999, ["N1"], id="other_year_excluded"),
        pytest.param(None, ["N2", "N1"], id="unlimited_before_the_years"),
    ],
)
def test_expense_name_year(main_user, second_valid_for, expect):
    ExpenseNameFactory(title="N1", valid_for=2000)
    ExpenseNameFactory(title="N2", valid_for=second_valid_for)

    actual = ExpenseNameModelService(main_user).year(2000)

    assert [a.title for a in actual] == expect


@pytest.mark.parametrize(("first", "second"), [("N1", "N1"), ("Būstas", "Bustas")])
def test_expense_name_slug_unique_per_parent(first, second):
    obj1 = ExpenseNameFactory(title=first)

    with pytest.raises(IntegrityError):
        ExpenseName(title=second, parent=obj1.parent).save()


def test_expense_name_longest_title_is_valid_with_its_slug():
    obj = ExpenseNameFactory(title="a" * 254)

    obj.full_clean()


def test_expense_str():
    expense = ExpenseFactory.build()

    assert str(expense) == "1999-01-01/Expense Type/Expense Name"


@override_storage()
def test_expense_stores_every_field():
    saved = ExpenseFactory(
        date=date(1998, 2, 3),
        price=1234,
        quantity=7,
        remark="R",
        exception=True,
        attachment=ContentFile(b"x", name="test1.jpg"),
    )

    actual = Expense.objects.get(pk=saved.pk)

    assert actual.date == date(1998, 2, 3)
    assert actual.price == 1234
    assert actual.quantity == 7
    assert actual.remark == "R"
    assert actual.exception is True
    assert actual.expense_type == saved.expense_type
    assert actual.expense_name == saved.expense_name
    assert actual.account == saved.account
    assert actual.attachment.read() == b"x"


@pytest.mark.parametrize(
    "fields, expect",
    [
        pytest.param({"price": -1}, ["price"], id="negative_price"),
        pytest.param({"remark": "R" * 1000}, [], id="long_remark"),
    ],
)
def test_expense_full_clean_accepts_only_what_its_columns_hold(fields, expect):
    expense = ExpenseFactory.build(**fields)

    errors = []
    try:
        expense.full_clean(exclude=["expense_type", "expense_name", "account"])
    except ValidationError as error:
        errors = list(error.message_dict)

    assert errors == expect


@override_storage()
@time_machine.travel("1974-1-1")
def test_expense_attachment_field(main_user):
    expense = ExpenseFactory(attachment=ContentFile(b"x", name="test1.jpg"))
    pk = str(main_user.journal.pk)

    assert (
        str(expense.attachment) == f"{pk}/{expense.expense_type.pk}/1974.01_test1.jpg"
    )


@override_storage()
@time_machine.travel("1974-1-1")
def test_expense_attachment_keeps_its_path_after_type_rename():
    expense = ExpenseFactory(attachment=ContentFile(b"x", name="test1.jpg"))
    stored = expense.attachment.name

    expense.expense_type.title = "Renamed"
    expense.expense_type.save()
    expense.save()

    assert Expense.objects.get(pk=expense.pk).attachment.name == stored


@factory.django.mute_signals(post_save)
def test_expense_related(main_user, second_user):
    main_account = AccountFactory(title="A1")
    second_account = AccountFactory(title="A2", journal=second_user.journal)
    main_type = ExpenseTypeFactory(title="T1")
    second_type = ExpenseTypeFactory(title="T2", journal=second_user.journal)

    ExpenseFactory(expense_type=main_type, account=main_account)
    ExpenseFactory(expense_type=second_type, account=second_account)

    actual = ExpenseModelService(main_user).items()

    assert [str(a.expense_type) for a in actual] == ["T1"]


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
def test_expense_last_months(main_user):
    ExpenseFactory(date=date(1998, 11, 30), price=3)
    ExpenseFactory(date=date(1998, 12, 31), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=7)

    actual = ExpenseModelService(main_user).last_months(TODAY, 6)

    assert [(a["sum"], a["title"]) for a in actual] == [(11, "Expense Type")]


@factory.django.mute_signals(post_save)
def test_expense_last_months_empty_expenses(main_user):
    ExpenseTypeFactory()

    actual = ExpenseModelService(main_user).last_months(TODAY, 6)
    assert not actual


@factory.django.mute_signals(post_save)
def test_expense_last_months_one_of_expenses_empty(main_user):
    used_type = ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2")

    ExpenseFactory(date=date(1999, 1, 1), price=3, expense_type=used_type)

    actual = ExpenseModelService(main_user).last_months(TODAY, 6)

    assert [(a["sum"], a["title"]) for a in actual] == [(3, "T1")]


@factory.django.mute_signals(post_save)
def test_expense_last_months_qs_count(main_user, django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1), price=2)

    with django_assert_max_num_queries(1):
        list(ExpenseModelService(main_user).last_months(TODAY))


@factory.django.mute_signals(post_save)
def test_expense_years_sum(main_user):
    ExpenseFactory(date=date(1998, 1, 1), price=4)
    ExpenseFactory(date=date(1998, 1, 1), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=5)
    ExpenseFactory(date=date(1999, 1, 1), price=5)

    actual = ExpenseModelService(main_user).sum_by_year()

    assert [(a["year"], a["sum"]) for a in actual] == [(1998, 8), (1999, 10)]


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


def account_balance_rows(*years):
    """Rows of the years named, or every year's row (the gap years too)."""
    qs = AccountBalance.objects.order_by("year")
    if years:
        qs = qs.filter(year__in=years)
    return [
        (a.account.title, a.year, a.past, a.incomes, a.expenses, a.balance, a.delta)
        for a in qs
    ]


def test_expense_new_post_save(main_user):
    ExpenseFactory(price=1)

    actual = AccountBalanceModelService(main_user).year(1999)

    assert [
        (a.account.title, a.past, a.incomes, a.expenses, a.balance) for a in actual
    ] == [("Account1", 0, 0, 1, -1)]


@pytest.mark.parametrize(
    "account_title, price_before, price_after",
    [
        pytest.param("Account1", 5, 5, id="nothing_changed"),
        pytest.param("Account1", 112, 1, id="price"),
        pytest.param("XXX", 5, 5, id="account"),
    ],
)
def test_expense_post_save_update(account_title, price_before, price_after):
    accounts = {t: AccountFactory(title=t) for t in ("Account1", "XXX")}
    obj = ExpenseFactory(price=price_before, account=accounts["Account1"])

    assert account_balance_rows(1999) == [
        ("Account1", 1999, 0, 0, price_before, -price_before, price_before)
    ]

    obj_update = Expense.objects.get(pk=obj.pk)
    obj_update.account = accounts[account_title]
    obj_update.price = price_after
    obj_update.save()

    assert account_balance_rows(1999) == [
        (account_title, 1999, 0, 0, price_after, -price_after, price_after)
    ]


def test_expense_post_save_update_object_user_model_year(main_user):
    assert date(1999, 1, 1) == Journal.objects.get(pk=main_user.journal.pk).first_record

    obj = ExpenseFactory(price=5)

    instance = Expense.objects.get(pk=obj.pk)

    instance.date = date(1974, 2, 3)
    instance.save()

    assert date(1974, 2, 3) == Journal.objects.get(pk=main_user.journal.pk).first_record


def test_expense_post_save_first_year_record():
    ExpenseFactory(date=date(1974, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    ExpenseFactory(date=date(1999, 1, 1), price=1)

    assert account_balance_rows(1974, 1999) == [
        ("Account1", 1974, 0, 0, 5, -5, 5),
        ("Account1", 1999, -5, 0, 1, -6, 6),
    ]


@pytest.mark.parametrize(
    "prior, before, after",
    [
        pytest.param(
            [],
            [("Account1", 1999, 0, 0, 1, -1, 1)],
            [],
            id="the_only_expense",
        ),
        pytest.param(
            [date(1974, 1, 1)],
            [("Account1", 1974, 0, 0, 5, -5, 5), ("Account1", 1999, -5, 0, 1, -6, 6)],
            [("Account1", 1974, 0, 0, 5, -5, 5)],
            id="another_year_remains",
        ),
    ],
)
def test_expense_post_delete(prior, before, after):
    for day in prior:
        ExpenseFactory(date=day, price=5)
    obj = ExpenseFactory(date=date(1999, 1, 1), price=1)

    assert account_balance_rows(1974, 1999) == before

    Expense.objects.get(pk=obj.pk).delete()

    assert account_balance_rows(1974, 1999) == after
    assert Expense.objects.count() == len(prior)


def test_expense_post_delete_empty_account_balance_table():
    ExpenseFactory(date=date(1974, 1, 1), price=5)
    obj = ExpenseFactory(date=date(1999, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    Expense.objects.get(pk=obj.pk).delete()

    assert account_balance_rows() == [
        ("Account1", 1974, 0, 0, 5, -5, 5),
        ("Account1", 1975, -5, 0, 0, -5, 5),
    ]


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

    assert [(a["year"], a["title"], a["sum"]) for a in actual] == [
        (1111, title, 5),
        (1999, title, 12),
    ]


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

    assert [(a["year"], a["title"], a["sum"]) for a in actual] == [
        (1111, title, 5),
        (1999, title, 12),
    ]


@factory.django.mute_signals(post_save)
def test_expenses(main_user, expenses):
    account1 = Account.objects.get(title="Account1")
    account2 = Account.objects.get(title="Account2")

    actual = ExpenseModelService(main_user).expenses()

    assert [(a["year"], a["category_id"], a["expenses"]) for a in actual] == [
        (1970, account1.pk, 250),
        (1970, account2.pk, 225),
        (1999, account1.pk, 50),
        (1999, account2.pk, 125),
    ]


@factory.django.mute_signals(post_save)
def test_sum_by_day_and_type_basic_grouping(main_user):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")

    ExpenseFactory(date=date(1999, 1, 1), price=10, expense_type=t1)
    ExpenseFactory(date=date(1999, 1, 1), price=20, expense_type=t1)
    ExpenseFactory(date=date(1999, 1, 1), price=50, expense_type=t2)
    ExpenseFactory(date=date(1999, 1, 2), price=100, expense_type=t1)

    actual = list(ExpenseModelService(main_user).sum_by_day_and_type(1999, 1))

    assert [(a["date"], a["title"], a["sum"], a["exception_sum"]) for a in actual] == [
        (date(1999, 1, 1), "T1", 30, 0),
        (date(1999, 1, 1), "T2", 50, 0),
        (date(1999, 1, 2), "T1", 100, 0),
    ]


@factory.django.mute_signals(post_save)
def test_sum_by_day_and_type_calculates_exceptions(main_user):
    t1 = ExpenseTypeFactory(title="T1")

    ExpenseFactory(date=date(1999, 1, 1), price=15, expense_type=t1, exception=1)
    ExpenseFactory(date=date(1999, 1, 1), price=25, expense_type=t1, exception=0)

    actual = list(ExpenseModelService(main_user).sum_by_day_and_type(1999, 1))

    assert [(a["sum"], a["exception_sum"]) for a in actual] == [(40, 15)]


@factory.django.mute_signals(post_save)
def test_sum_by_day_and_type_ignores_other_dates(main_user):
    t1 = ExpenseTypeFactory(title="T1")

    ExpenseFactory(date=date(1999, 1, 15), price=10, expense_type=t1)
    ExpenseFactory(date=date(1999, 2, 15), price=20, expense_type=t1)
    ExpenseFactory(date=date(1998, 1, 15), price=30, expense_type=t1)

    actual = list(ExpenseModelService(main_user).sum_by_day_and_type(1999, 1))

    assert [(a["date"], a["sum"]) for a in actual] == [(date(1999, 1, 15), 10)]


@pytest.mark.parametrize(
    "lang, expected",
    [
        pytest.param("lt", "1.234,56", id="lt"),
        pytest.param("en", "1,234.56", id="en"),
    ],
)
def test_expenses_list_dynamic_locale(main_user, lang, expected):
    main_user.journal.lang = lang
    main_user.journal.save()

    ExpenseFactory(price=123456)

    qs = ExpenseModelService(main_user).items()
    actual = list(ExpenseModelService(main_user).expenses_list(qs))

    assert [a["price_str"] for a in actual] == [expected]


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


def test_expense_keyword_clean_asks_the_db_once(main_user, django_assert_num_queries):
    name = ExpenseNameFactory(parent=ExpenseTypeFactory(journal=main_user.journal))
    obj = ExpenseKeyword(journal=main_user.journal, expense_name_id=name.pk)

    with django_assert_num_queries(1):
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


@pytest.mark.parametrize(
    "own_titles", [(), ("Kita",)], ids=["plain", "same_titled_own_name"]
)
def test_expense_keyword_clean_refuses_a_name_of_another_journal(
    main_user, second_user, own_titles
):
    own_type = ExpenseTypeFactory(title="Maistas", journal=main_user.journal)
    for title in own_titles:
        ExpenseNameFactory(title=title, parent=own_type)
    other_type = ExpenseTypeFactory(title="Buitinės", journal=second_user.journal)
    name = ExpenseNameFactory(title="Kita", parent=other_type)
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
