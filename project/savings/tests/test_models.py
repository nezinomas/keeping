from datetime import date
from importlib import import_module

import factory
import pytest
import time_machine
from django.apps import apps
from django.db import IntegrityError, connection
from django.db.models.signals import post_delete, post_save
from django.test.utils import CaptureQueriesContext

from ...accounts.models import AccountBalance
from ...accounts.services.model_services import AccountBalanceModelService
from ...accounts.tests.factories import AccountFactory
from ...bookkeeping.tests.factories import SavingWorthFactory
from ...incomes.tests.factories import IncomeFactory
from ...savings.tests.factories import (
    SavingBalanceFactory,
    SavingFactory,
    SavingTypeFactory,
)
from ..models import Saving, SavingBalance, SavingType
from ..services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
    SavingTypeModelService,
)

pytestmark = pytest.mark.django_db

TODAY = date(1999, 6, 1)

slug_migration = import_module(
    "project.savings.migrations.0017_savingtype_savings_savingtype_unique_slug"
)


@pytest.fixture(name="savings_extra")
def fixture_savings_extra():
    SavingFactory(
        date=date(1999, 1, 1),
        price=1,
        fee=0.25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=1,
        fee=0.25,
        account=AccountFactory(title="Account2"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )


def test_saving_str():
    i = SavingFactory.build()

    assert str(i) == "1999-01-01: Savings"


@pytest.mark.parametrize(
    "fields, expect",
    [
        pytest.param({}, "investment", id="defaults_to_investment"),
        pytest.param(
            {"fee_source": SavingType.FeeSource.ACCOUNT}, "account", id="the_account"
        ),
    ],
)
def test_saving_type_fee_source(fields, expect):
    actual = SavingTypeFactory(**fields)

    actual.refresh_from_db()
    assert actual.fee_source == expect


@pytest.mark.parametrize(
    "read, expect_titles",
    [
        pytest.param(
            lambda user: list(SavingTypeModelService(user).items()),
            ["T1"],
            id="saving_type",
        ),
        pytest.param(
            lambda user: [s.saving_type for s in SavingModelService(user).objects],
            ["T1"],
            id="saving",
        ),
        pytest.param(
            lambda user: [
                b.saving_type for b in SavingBalanceModelService(user).year(1999)
            ],
            ["T1"],
            id="saving_balance",
        ),
    ],
)
def test_savings_services_read_only_their_journal(
    main_user, second_user, read, expect_titles
):
    for user, title in ((main_user, "T1"), (second_user, "T2")):
        SavingFactory(
            saving_type=SavingTypeFactory(title=title, journal=user.journal),
            account=AccountFactory(title=f"A-{title}", journal=user.journal),
        )

    actual = read(main_user)

    assert [t.title for t in actual] == expect_titles
    assert all(t.journal == main_user.journal for t in actual)


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "kwargs", [{"year": 1999}, {}], ids=["given_year", "year_from_get_user"]
)
def test_saving_type_items_filter_closed_in_future(main_user, kwargs):
    SavingTypeFactory(title="T1", closed=1998)
    SavingTypeFactory(title="T2", closed=2000)

    actual = SavingTypeModelService(main_user).items(**kwargs)

    assert [row.title for row in actual] == ["T2"]


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "user_year, expect",
    [(3000, 1), (1000, 2), (2000, 2)],
    ids=["after_closed", "before_closed", "closed_year"],
)
def test_saving_type_items_closed(main_user, user_year, expect):
    main_user.year = user_year
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    actual = SavingTypeModelService(main_user).items()

    assert actual.count() == expect


@pytest.mark.parametrize(
    "first, second",
    [
        pytest.param("T1", "T1", id="title"),
        pytest.param("Būstas", "Bustas", id="slug"),
    ],
)
def test_saving_type_unique_for_journal(main_user, first, second):
    SavingType.objects.create(title=first, journal=main_user.journal)

    with pytest.raises(IntegrityError):
        SavingType.objects.create(title=second, journal=main_user.journal)


def test_saving_type_unique_for_journals(main_user, second_user):
    SavingType.objects.create(title="T1", journal=main_user.journal)
    SavingType.objects.create(title="T1", journal=second_user.journal)

    assert SavingType.objects.filter(title="T1").count() == 2


def test_saving_type_save_writes_slug(main_user):
    actual = SavingType.objects.create(title="Finbee", journal=main_user.journal)

    assert actual.slug == "finbee"


def test_saving_type_migration_fills_every_slug(main_user):
    SavingType.objects.create(title="Finbee", journal=main_user.journal)
    SavingType.objects.create(title="VGWL - Vanguard", journal=main_user.journal)
    SavingType.objects.filter(title="Finbee").update(slug="")
    SavingType.objects.exclude(title="Finbee").update(slug="vgwl")

    slug_migration.fill_slugs(apps, None)

    actual = list(SavingType.objects.order_by("title").values_list("slug", flat=True))
    assert actual == ["finbee", "vgwl-vanguard"]


def test_saving_without_price_or_fee_stores_zero():
    saving = Saving.objects.create(
        date=date(1999, 1, 1),
        account=AccountFactory(),
        saving_type=SavingTypeFactory(),
    )

    saving.refresh_from_db()
    assert saving.price == 0
    assert saving.fee == 0


def test_saving_type_str():
    actual = SavingTypeFactory.build()

    assert str(actual) == "Savings"


@factory.django.mute_signals(post_save)
def test_saving_items(main_user):
    SavingFactory()

    assert len(SavingModelService(main_user).items()) == 1


@factory.django.mute_signals(post_save)
def test_saving_years_sum(main_user):
    SavingFactory(date=date(1998, 1, 1), price=4.0)
    SavingFactory(date=date(1998, 1, 1), price=4.0)
    SavingFactory(date=date(1999, 1, 1), price=5.0)
    SavingFactory(date=date(1999, 1, 1), price=5.0)

    actual = SavingModelService(main_user).sum_by_year()

    assert [(row["year"], row["sum"]) for row in actual] == [(1998, 8.0), (1999, 10.0)]


@pytest.mark.parametrize(
    "read, expect",
    [
        pytest.param(
            lambda s: [(r["year"], r["sum"]) for r in s.sum_by_year()],
            [(1999, 2)],
            id="year_sum",
        ),
        pytest.param(lambda s: s.last_months(TODAY), {"sum": 2}, id="last_months"),
    ],
)
def test_saving_read_query_count(
    main_user, django_assert_max_num_queries, read, expect
):
    SavingFactory(date=date(1999, 1, 1), price=2)

    with django_assert_max_num_queries(1):
        actual = read(SavingModelService(main_user))
    assert actual == expect


@factory.django.mute_signals(post_save, post_delete)
@pytest.mark.parametrize(
    "sums, expect",
    [
        pytest.param(
            lambda s: s.sum_by_month_and_type(1999),
            [
                {"date": date(1999, 1, 1), "sum": 350, "title": "Saving1"},
                {"date": date(1999, 1, 1), "sum": 225, "title": "Saving2"},
            ],
            id="month_and_type",
        ),
        pytest.param(
            lambda s: s.sum_by_day_and_type(1999, 1),
            [
                {"date": date(1999, 1, 1), "sum": 350, "title": "Saving1"},
                {"date": date(1999, 1, 1), "sum": 225, "title": "Saving2"},
            ],
            id="day_and_type",
        ),
        pytest.param(lambda s: s.sum_by_day_and_type(1999, 2), [], id="empty_month"),
        pytest.param(
            lambda s: s.sum_by_month(1999),
            [{"date": date(1999, 1, 1), "sum": 575, "title": "savings"}],
            id="month",
        ),
    ],
)
def test_saving_sums_of_the_fixture_savings(main_user, savings, sums, expect):
    actual = list(sums(SavingModelService(main_user)))

    assert expect == actual


@factory.django.mute_signals(post_save)
def test_saving_day_sum(main_user, savings_extra):
    expect = [
        {"date": date(1999, 1, 1), "sum": 2, "title": "savings"},
    ]

    actual = list(SavingModelService(main_user).sum_by_day(1999, 1))

    assert expect == actual


def test_saving_months_sum_takes_no_month(main_user):
    with pytest.raises(TypeError):
        SavingModelService(main_user).sum_by_month(1999, 1)


@pytest.mark.parametrize(
    "query",
    [
        pytest.param(lambda s: s.items().values(), id="items"),
        pytest.param(lambda s: s.year(1999).values(), id="year"),
        pytest.param(lambda s: s.sum_by_month(1999).values(), id="month_saving"),
        pytest.param(
            lambda s: s.sum_by_month_and_type(1999).values(), id="month_type_sum"
        ),
        pytest.param(
            lambda s: s.sum_by_day_and_type(1999, 1).values(), id="day_saving_type"
        ),
        pytest.param(lambda s: s.sum_by_day(1999, 1).values(), id="day_saving"),
    ],
)
def test_saving_query_count(main_user, django_assert_max_num_queries, query):
    with django_assert_max_num_queries(1):
        query(SavingModelService(main_user))


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "savings, expect",
    [
        (
            [(date(1998, 11, 30), 3), (date(1998, 12, 31), 4), (date(1999, 1, 1), 7)],
            11,
        ),
        ([], 0),
    ],
    ids=["sums_the_window", "empty_savings"],
)
def test_saving_last_months(main_user, savings, expect):
    SavingTypeFactory()
    for day, price in savings:
        SavingFactory(date=day, price=price)

    actual = SavingModelService(main_user).last_months(TODAY, 6)

    assert actual["sum"] == expect


@pytest.mark.parametrize("price, fee", [(150, 5), (10, 2)])
def test_saving_post_save(main_user, price, fee):
    SavingFactory(
        saving_type=SavingTypeFactory(title="S"),
        account=AccountFactory(title="A"),
        price=price,
        fee=fee,
    )

    actual = AccountBalanceModelService(main_user).year(1999)
    assert [
        (a.account.title, a.past, a.incomes, a.expenses, a.balance) for a in actual
    ] == [("A", 0, 0, price, -price)]

    actual = SavingBalanceModelService(main_user).year(1999)
    assert [
        (a.saving_type.title, a.past_amount, a.past_fee, a.fee, a.incomes)
        for a in actual
    ] == [("S", 0, 0, fee, price)]


@pytest.mark.parametrize(
    "account, saving_type, price, fee",
    [
        pytest.param("A", "S", 10, 2, id="nothing_changed"),
        pytest.param("A", "S", 4, 1, id="amounts"),
        pytest.param("A", "S-New", 10, 2, id="saving_type"),
        pytest.param("A-New", "S", 10, 2, id="account"),
        pytest.param("A-New", "S-New", 10, 2, id="account_and_saving_type"),
    ],
)
def test_saving_post_save_update(account, saving_type, price, fee):
    accounts = {t: AccountFactory(title=t) for t in ("A", "A-New")}
    saving_types = {t: SavingTypeFactory(title=t) for t in ("S", "S-New")}
    obj = SavingFactory(
        saving_type=saving_types["S"], account=accounts["A"], price=10, fee=2
    )

    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.account = accounts[account]
    obj_update.saving_type = saving_types[saving_type]
    obj_update.price = price
    obj_update.fee = fee
    obj_update.save()

    actual = AccountBalance.objects.filter(year=1999)
    assert [
        (a.account.title, a.past, a.incomes, a.expenses, a.balance) for a in actual
    ] == [(account, 0, 0, price, -price)]

    actual = SavingBalance.objects.filter(year=1999)
    assert [
        (a.saving_type.title, a.past_amount, a.past_fee, a.fee, a.incomes)
        for a in actual
    ] == [(saving_type, 0, 0, fee, price)]


def test_saving_post_save_first_record():
    _a = AccountFactory(title="A")
    _s = SavingTypeFactory(title="S")

    SavingFactory(saving_type=_s, account=_a, price=4, date=date(1998, 1, 1), fee=2)
    IncomeFactory(account=_a, price=3, date=date(1998, 1, 1))

    SavingBalance.objects.all().delete()
    AccountBalance.objects.all().delete()

    SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == -1
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -11

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 4
    assert actual.past_fee == 2
    assert actual.fee == 4
    assert actual.incomes == 14


def test_saving_post_save_different_types():
    s1 = SavingTypeFactory(title="1")
    s2 = SavingTypeFactory(title="2")

    SavingFactory(saving_type=s1, price=150)
    SavingFactory(saving_type=s2, price=250)

    actual = Saving.objects.all()
    assert actual.count() == 2

    actual = AccountBalance.objects.order_by("year", "pk")
    assert [(a.year, a.incomes, a.expenses) for a in actual] == [
        (1999, 0, 400),
        (2000, 0, 0),
    ]
    actual = SavingBalance.objects.order_by("year", "saving_type__title")
    assert [(a.year, a.saving_type.title, a.incomes, a.fee) for a in actual] == [
        (1999, "1", 150, 5),
        (1999, "2", 250, 5),
        (2000, "1", 150, 5),
        (2000, "2", 250, 5),
    ]


@pytest.mark.parametrize(
    "prior_prices, account_rows, saving_rows",
    [
        pytest.param([], [], [], id="the_only_saving"),
        pytest.param(
            [10], [("Account1", 10, -10)], [(5, 10)], id="another_saving_remains"
        ),
    ],
)
def test_saving_post_delete(main_user, prior_prices, account_rows, saving_rows):
    for price in prior_prices:
        SavingFactory(price=price)
    obj = SavingFactory()

    Saving.objects.get(pk=obj.pk).delete()

    actual = AccountBalanceModelService(main_user).year(1999)
    assert [(a.account.title, a.expenses, a.balance) for a in actual] == account_rows

    actual = SavingBalanceModelService(main_user).year(1999)
    assert [(a.fee, a.incomes) for a in actual] == saving_rows

    assert Saving.objects.count() == len(prior_prices)


@factory.django.mute_signals(post_save, post_delete)
def test_savings_incomes(main_user, savings):
    SavingFactory(
        date=date(1999, 1, 1),
        price=225,
        fee=25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving2"),
    )

    actual = SavingModelService(main_user).incomes()

    assert [(r["year"], r["category_id"], r["incomes"], r["fee"]) for r in actual] == [
        (1970, 1, 125, 25),
        (1970, 2, 25, 0),
        (1999, 1, 350, 50),
        (1999, 2, 450, 50),
    ]


@factory.django.mute_signals(post_save)
def test_savings_expenses(main_user, savings):
    actual = SavingModelService(main_user).expenses()

    assert [(r["year"], r["category_id"], r["expenses"]) for r in actual] == [
        (1970, 1, 125),
        (1970, 2, 25),
        (1999, 1, 350),
        (1999, 2, 225),
    ]


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "fee_source, expect",
    [(SavingType.FeeSource.INVESTMENT, 0), (SavingType.FeeSource.ACCOUNT, 100)],
)
def test_a_fee_only_purchase_expenses_and_incomes(main_user, fee_source, expect):
    Saving.objects.create(
        date=date(1999, 1, 1),
        fee=100,
        account=AccountFactory(),
        saving_type=SavingTypeFactory(fee_source=fee_source),
    )
    service = SavingModelService(main_user)

    assert [r["expenses"] for r in service.expenses()] == [expect]
    assert [r["incomes"] for r in service.incomes()] == [0]


def test_saving_balance_init():
    actual = SavingBalanceFactory.build()

    assert actual.past_amount == 20
    assert actual.past_fee == 21
    assert actual.fee == 22
    assert actual.incomes == 24
    assert actual.market_value == 25
    assert actual.profit_sum == 29


def test_saving_balance_str():
    actual = SavingBalanceFactory.build()

    assert str(actual) == "Savings"


def test_saving_balance_year(main_user):
    SavingBalanceFactory(year=1998)
    SavingBalanceFactory(year=1999)
    SavingBalanceFactory(year=2000)

    actual = SavingBalanceModelService(main_user).year(1999)

    assert len(actual) == 1


def test_saving_balance_items_queries(main_user, django_assert_num_queries):
    s1 = SavingTypeFactory(title="s1")
    s2 = SavingTypeFactory(title="s2")

    SavingBalanceFactory(saving_type=s1)
    SavingBalanceFactory(saving_type=s2)

    with django_assert_num_queries(1):
        list(SavingBalanceModelService(main_user).items().values())


@pytest.mark.parametrize(
    "types, expect_titles",
    [
        pytest.param(["x"], ["1"], id="one_type"),
        pytest.param(["x", "y"], ["1", "2"], id="few_types"),
    ],
)
def test_saving_balance_filter_by_types(main_user, types, expect_titles):
    SavingFactory(saving_type=SavingTypeFactory(title="1", type="x"))
    SavingFactory(saving_type=SavingTypeFactory(title="2", type="y"))
    SavingFactory(saving_type=SavingTypeFactory(title="3", type="z"))

    actual = SavingBalanceModelService(main_user).year_of_types(1999, types)

    assert [a.saving_type.title for a in actual] == expect_titles
    assert [(a.incomes, a.fee) for a in actual] == [(150, 5)] * len(expect_titles)


def test_saving_balance_year_takes_no_types(main_user):
    with pytest.raises(TypeError):
        SavingBalanceModelService(main_user).year(1999, ["x"])


@pytest.mark.parametrize(
    "funds, expect_titles",
    [
        pytest.param([("1", "x"), ("2", "z")], ["1", "2"], id="every_type"),
        pytest.param([("B", "x"), ("A", "x")], ["A", "B"], id="one_type_by_title"),
    ],
)
def test_saving_balance_year_orders_by_type_then_title(main_user, funds, expect_titles):
    for title, fund_type in funds:
        SavingFactory(saving_type=SavingTypeFactory(title=title, type=fund_type))

    actual = SavingBalanceModelService(main_user).year(1999)

    assert [a.saving_type.title for a in actual] == expect_titles


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("fund_type", ["funds", "shares", "pensions"])
def test_sum_by_type(main_user, fund_type):
    f = SavingTypeFactory(title="F", type=fund_type)

    SavingFactory(saving_type=f, price=1, fee=1)
    SavingFactory(saving_type=f, price=10, fee=1)
    SavingWorthFactory(saving_type=f, price=20)

    actual = list(SavingBalanceModelService(main_user).sum_by_type())

    assert actual == [
        {
            "year": year,
            "incomes": 11,
            "profit": 7,
            "total": 20,
            "fee": 2,
            "type": fund_type,
        }
        for year in (1999, 2000)
    ]


@time_machine.travel("1999-1-1")
def test_sum_by_year(main_user):
    f = SavingTypeFactory(title="F", type="funds")
    p = SavingTypeFactory(title="P", type="pensions")
    s = SavingTypeFactory(title="S", type="shares")

    SavingFactory(saving_type=f, price=1, fee=0)
    SavingFactory(saving_type=p, price=2, fee=0)
    SavingFactory(saving_type=s, price=4, fee=0)

    actual = list(SavingBalanceModelService(main_user).sum_by_year())

    assert actual == [
        {"year": 1999, "incomes": 7, "profit": -7},
        {"year": 2000, "incomes": 7, "profit": -7},
    ]


def test_saving_balance_sorting(main_user):
    s1 = SavingTypeFactory(title="1")
    s2 = SavingTypeFactory(title="2")

    SavingBalanceFactory(year=2000, saving_type=s2)
    SavingBalanceFactory(year=1999, saving_type=s2)
    SavingBalanceFactory(year=2000, saving_type=s1)
    SavingBalanceFactory(year=1999, saving_type=s1)

    actual = SavingBalanceModelService(main_user).objects

    assert [(row.year, row.saving_type.title) for row in actual] == [
        (1999, "1"),
        (1999, "2"),
        (2000, "1"),
        (2000, "2"),
    ]


SAVINGS_SUMS = {
    "sum_by_year": lambda s: list(s.sum_by_year()),
    "sum_by_month": lambda s: list(s.sum_by_month(1999)),
    "sum_by_day": lambda s: list(s.sum_by_day(1999, 1)),
    "sum_by_month_and_type": lambda s: list(s.sum_by_month_and_type(1999)),
    "sum_by_day_and_type": lambda s: list(s.sum_by_day_and_type(1999, 1)),
    "last_months": lambda s: [s.last_months(TODAY, 6)],
}


def _rows(user, name):
    return SAVINGS_SUMS[name](SavingModelService(user))


def _single_sum(user, name):
    rows = _rows(user, name)
    assert len(rows) == 1
    return rows[0]["sum"]


def _fee_purchase(fee_source, price, fee, title="Fund"):
    SavingFactory(
        price=price,
        fee=fee,
        saving_type=SavingTypeFactory(title=title, fee_source=fee_source),
    )


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize("name", SAVINGS_SUMS)
@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
@pytest.mark.parametrize(
    "price, fee, expect",
    [(20000, 300, 20000), (0, 100, 0)],
    ids=["invested_price", "fee_only_row"],
)
def test_savings_sums_show_the_price_never_the_fee(
    main_user, name, fee_source, price, fee, expect
):
    _fee_purchase(fee_source, price, fee)

    assert _single_sum(main_user, name) == expect


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
def test_incomes_ignore_the_fee_source(main_user, fee_source):
    _fee_purchase(fee_source, 20000, 300)

    actual = list(SavingModelService(main_user).incomes())

    assert [(r["incomes"], r["fee"]) for r in actual] == [(20000, 300)]


ACCOUNT_FEES_READS = {
    "month": lambda s: list(s.account_fees_by_month(1999)),
    "day": lambda s: list(s.account_fees_by_day(1999, 1)),
}
FEE_FROM_ACCOUNT = SavingType.FeeSource.ACCOUNT
FEE_FROM_INVESTMENT = SavingType.FeeSource.INVESTMENT
JANUARY_ACCOUNT_FEES = [
    {"date": date(1999, 1, 1), "sum": 428, "title": "savings_account_fee"}
]


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "read, purchases, expect",
    [
        (
            "month",
            [
                (FEE_FROM_ACCOUNT, date(1999, 1, 1), 20000, 300),
                (FEE_FROM_ACCOUNT, date(1999, 1, 1), 0, 128),
                (FEE_FROM_ACCOUNT, date(1999, 1, 1), 500, 0),
                (FEE_FROM_INVESTMENT, date(1999, 1, 1), 1000, 100),
            ],
            JANUARY_ACCOUNT_FEES,
        ),
        (
            "day",
            [
                (FEE_FROM_ACCOUNT, date(1999, 1, 1), 20000, 300),
                (FEE_FROM_ACCOUNT, date(1999, 1, 1), 500, 128),
                (FEE_FROM_INVESTMENT, date(1999, 1, 1), 1000, 100),
            ],
            JANUARY_ACCOUNT_FEES,
        ),
        ("month", [(FEE_FROM_ACCOUNT, date(1999, 1, 1), 500, 0)], []),
        ("day", [(FEE_FROM_ACCOUNT, date(1999, 1, 1), 500, 0)], []),
        ("month", [(FEE_FROM_INVESTMENT, date(1999, 1, 1), 1000, 100)], []),
        ("month", [(FEE_FROM_ACCOUNT, date(2000, 1, 1), 0, 300)], []),
        ("day", [(FEE_FROM_ACCOUNT, date(1999, 2, 1), 0, 300)], []),
    ],
    ids=[
        "month_sums_only_account_charged",
        "day_sums_only_account_charged",
        "month_ignores_a_zero_fee",
        "day_ignores_a_zero_fee",
        "month_empty_without_account_charged",
        "month_reads_only_its_year",
        "day_reads_only_its_month",
    ],
)
def test_account_fees(main_user, read, purchases, expect):
    for i, (fee_source, day, price, fee) in enumerate(purchases):
        SavingFactory(
            date=day,
            price=price,
            fee=fee,
            saving_type=SavingTypeFactory(title=f"T{i}", fee_source=fee_source),
        )

    assert ACCOUNT_FEES_READS[read](SavingModelService(main_user)) == expect


@factory.django.mute_signals(post_save)
def test_cash_flow_by_month_holds_both_series_in_one_query(main_user):
    _fee_purchase(SavingType.FeeSource.ACCOUNT, 20000, 300, title="VALL")
    _fee_purchase(SavingType.FeeSource.INVESTMENT, 1000, 100, title="Finbee")

    with CaptureQueriesContext(connection) as ctx:
        actual = list(SavingModelService(main_user).cash_flow_by_month(1999))

    assert len(ctx) == 1
    assert sorted((row["title"], row["sum"]) for row in actual) == [
        ("savings", 21000),
        ("savings_account_fee", 300),
    ]


SUMS_UNDER_A_QUERY_GUARD = SAVINGS_SUMS | {
    "account_fees_by_month": lambda s: list(s.account_fees_by_month(1999)),
}


def _purchases_of_both_fee_sources(start, stop):
    sources = [SavingType.FeeSource.ACCOUNT, SavingType.FeeSource.INVESTMENT]
    for i in range(start, stop):
        SavingFactory(
            price=150,
            fee=5,
            saving_type=SavingTypeFactory(title=f"T{i}", fee_source=sources[i % 2]),
        )


def _queries_and_total(user, name):
    with CaptureQueriesContext(connection) as ctx:
        rows = SUMS_UNDER_A_QUERY_GUARD[name](SavingModelService(user))
    return len(ctx), sum(row["sum"] for row in rows)


@factory.django.mute_signals(post_save)
@pytest.mark.parametrize(
    "name, per_fund, per_account_fund",
    [(name, 150, 0) for name in SAVINGS_SUMS] + [("account_fees_by_month", 0, 5)],
    ids=[*SAVINGS_SUMS, "account_fees_by_month"],
)
def test_sum_query_count_does_not_grow_and_every_fund_is_counted(
    main_user, name, per_fund, per_account_fund
):
    _purchases_of_both_fee_sources(0, 2)
    two, total = _queries_and_total(main_user, name)
    assert total == 2 * per_fund + 1 * per_account_fund

    _purchases_of_both_fee_sources(2, 6)
    six, total = _queries_and_total(main_user, name)
    assert total == 6 * per_fund + 3 * per_account_fund
    assert six == two


@factory.django.mute_signals(post_save)
def test_spent_last_months_adds_only_account_charged_fees(main_user):
    SavingFactory(
        date=date(1998, 11, 30),
        price=1000,
        fee=1,
        saving_type=SavingTypeFactory(fee_source=SavingType.FeeSource.ACCOUNT),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=200,
        fee=7,
        saving_type=SavingTypeFactory(fee_source=SavingType.FeeSource.ACCOUNT),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=300,
        fee=100,
        saving_type=SavingTypeFactory(
            title="Finbee", fee_source=SavingType.FeeSource.INVESTMENT
        ),
    )

    actual = SavingModelService(main_user).spent_last_months(TODAY, 6)

    assert actual["sum"] == 507


def test_spent_last_months_is_zero_without_savings(main_user):
    assert SavingModelService(main_user).spent_last_months(TODAY, 6)["sum"] == 0


@pytest.mark.parametrize(
    "market_value, sold_since_check, expected",
    [(100, 0, True), (100, 40, False), (0, 0, False), (0, 40, False)],
)
def test_saving_balance_shows_profit_for_a_fresh_worth(
    market_value, sold_since_check, expected
):
    obj = SavingBalanceFactory.build(
        market_value=market_value, sold_since_check=sold_since_check
    )

    assert obj.shows_profit is expected


@pytest.mark.parametrize("sold, expected", [(10, True), (0, False)])
def test_saving_balance_shows_profit_in_the_close_year_with_a_sell(sold, expected):
    fund = SavingTypeFactory.build(closed=1999)
    obj = SavingBalanceFactory.build(
        saving_type=fund, year=1999, market_value=0, sold=sold
    )

    assert obj.shows_profit is expected


def test_saving_balance_shows_no_profit_for_a_sell_after_the_close_year():
    fund = SavingTypeFactory.build(closed=1998)
    obj = SavingBalanceFactory.build(
        saving_type=fund, year=1999, market_value=0, sold=10
    )

    assert obj.shows_profit is False


def test_saving_journal_is_its_types(second_user):
    journal = second_user.journal

    obj = SavingFactory.build(saving_type=SavingTypeFactory(journal=journal))

    assert obj.journal == journal
