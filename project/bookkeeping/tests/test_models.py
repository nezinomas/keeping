from datetime import datetime as dt
from typing import NamedTuple
from zoneinfo import ZoneInfo

import factory as factory_boy
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountBalanceFactory, AccountFactory
from ...pensions.models import PensionBalance
from ...pensions.tests.factories import PensionBalanceFactory, PensionTypeFactory
from ...savings.models import SavingBalance
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ..services.model_services import (
    AccountWorthModelService,
    PensionWorthModelService,
    SavingWorthModelService,
)
from .factories import AccountWorthFactory, PensionWorthFactory, SavingWorthFactory

pytestmark = pytest.mark.django_db


class Worth(NamedTuple):
    """A kind of worth: its model service, its factory, its owner's field and
    factory."""

    service: type
    factory: type[factory_boy.Factory]
    field: str
    owner_factory: type[factory_boy.Factory]


ACCOUNT, SAVING, PENSION = WORTHS = [
    Worth(AccountWorthModelService, AccountWorthFactory, "account", AccountFactory),
    Worth(
        SavingWorthModelService, SavingWorthFactory, "saving_type", SavingTypeFactory
    ),
    Worth(
        PensionWorthModelService,
        PensionWorthFactory,
        "pension_type",
        PensionTypeFactory,
    ),
]
WORTH_IDS = ["account", "saving", "pension"]
FUND_ZEROS = {"past_amount": 0, "past_fee": 0, "fee": 0, "incomes": 0}


@pytest.mark.parametrize(
    "worth, owner",
    list(zip(WORTHS, ["Account1", "Savings", "PensionType"], strict=True)),
    ids=WORTH_IDS,
)
def test_worth_str_reads_its_date_and_owner(worth, owner):
    assert str(worth.factory()) == f"1999-01-01 02:03 - {owner}"


@pytest.mark.parametrize(
    "worth, rows, count, fields",
    [
        (
            ACCOUNT,
            AccountBalance.objects.filter(year=1999),
            1,
            {"incomes": 0, "expenses": 0, "balance": 0, "have": 5, "delta": 5},
        ),
        (
            SAVING,
            SavingBalance.objects.all(),
            2,
            {"saving_type__title": "Savings", **FUND_ZEROS, "market_value": 5},
        ),
        (
            PENSION,
            PensionBalance.objects.all(),
            2,
            {"pension_type__title": "PensionType", **FUND_ZEROS, "market_value": 5},
        ),
    ],
    ids=WORTH_IDS,
)
def test_a_first_worth_writes_its_owners_balance(worth, rows, count, fields):
    worth.factory()

    assert (rows.count(), rows.values(*fields).first()) == (count, fields)


# the worth replaces what the balance had: 20 of cash, the fund's 25 market value
@pytest.mark.parametrize(
    "seed, worth, price, model, before, count, after",
    [
        (
            AccountBalanceFactory,
            ACCOUNT,
            5,
            AccountBalance,
            {"have": 20},
            2,
            {"have": 5},
        ),
        (
            lambda: SavingFactory(price=20, fee=5),
            SAVING,
            30,
            SavingBalance,
            {
                "saving_type__title": "Savings",
                "fee": 5,
                "incomes": 20,
                "market_value": 0,
            },
            2,
            {
                "saving_type__title": "Savings",
                "fee": 5,
                "incomes": 20,
                "market_value": 30,
            },
        ),
        (
            PensionBalanceFactory,
            PENSION,
            3,
            PensionBalance,
            {"pension_type__title": "PensionType", "market_value": 25},
            2,
            {"pension_type__title": "PensionType", "market_value": 3},
        ),
    ],
    ids=WORTH_IDS,
)
def test_a_new_worth_rewrites_its_owners_balance(
    seed, worth, price, model, before, count, after
):
    seed()
    rows = model.objects.all()
    first = rows.values(*before).first()

    worth.factory(price=price)

    assert (first, rows.count(), rows.values(*after).first()) == (before, count, after)


@pytest.mark.parametrize("worth", WORTHS, ids=WORTH_IDS)
def test_worth_objects_are_the_users_journals(main_user, second_user, worth):
    mine = worth.owner_factory(title="Mine")
    worth.factory(**{worth.field: mine})
    theirs = worth.owner_factory(title="Theirs", journal=second_user.journal)
    worth.factory(**{worth.field: theirs})

    actual = worth.service(main_user).objects

    assert [getattr(row, worth.field) for row in actual] == [mine]


def _two_years(first_2000, last_2000):
    """(date, price) of two worths in 1970 and two in 2000, the later one dearer."""
    return [
        (dt(1970, 1, 1, tzinfo=ZoneInfo("UTC")), 1),
        (dt(1970, 12, 31, tzinfo=ZoneInfo("UTC")), 2),
        (first_2000, 3),
        (last_2000, 4),
    ]


FUND_YEARS = _two_years(
    dt(2000, 1, 1, tzinfo=ZoneInfo("UTC")), dt(2000, 12, 31, tzinfo=ZoneInfo("UTC"))
)
LATEST = [(1970, 1, 2), (2000, 1, 4)]


# the account row's two 2000 worths share a day, so the later time is the latest
@pytest.mark.parametrize(
    "worth, seeds, have",
    [
        pytest.param(
            ACCOUNT,
            _two_years(
                dt(2000, 12, 31, 1, 1, 1, tzinfo=ZoneInfo("UTC")),
                dt(2000, 12, 31, 3, 2, 1, tzinfo=ZoneInfo("UTC")),
            ),
            LATEST,
            id="account",
        ),
        pytest.param(SAVING, FUND_YEARS, LATEST, id="saving"),
        pytest.param(PENSION, FUND_YEARS, LATEST, id="pension"),
        *[
            pytest.param(worth, [], [], id=f"{name}-none")
            for worth, name in zip(WORTHS, WORTH_IDS, strict=True)
        ],
    ],
)
def test_worth_have_is_each_years_latest_worth(main_user, worth, seeds, have):
    for date, price in seeds:
        worth.factory(date=date, price=price)

    actual = worth.service(main_user).have()

    assert [(x["year"], x["category_id"], x["have"]) for x in actual] == have


@pytest.mark.parametrize("worth", WORTHS, ids=WORTH_IDS)
def test_worth_price_is_never_null(worth):
    with pytest.raises(IntegrityError), transaction.atomic():
        worth.factory(price=None)


@pytest.mark.parametrize("worth", WORTHS, ids=WORTH_IDS)
def test_worth_price_is_required(worth):
    row = worth.factory.build(price=None)

    with pytest.raises(ValidationError):
        row._meta.get_field("price").clean(None, row)


@pytest.mark.parametrize("worth", WORTHS, ids=WORTH_IDS)
def test_worth_journal_is_its_owners(second_user, worth):
    journal = second_user.journal

    row = worth.factory.build(**{worth.field: worth.owner_factory(journal=journal)})

    assert row.journal == journal
