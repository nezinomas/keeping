from datetime import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from ...accounts.models import AccountBalance
from ...accounts.services.model_services import AccountBalanceModelService
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


# AccountWorth
def test_account_worth_str():
    actual = AccountWorthFactory()

    assert str(actual) == "1999-01-01 02:03 - Account1"


def test_account_worth_post_save(main_user):
    AccountWorthFactory(date=dt(1999, 1, 1, tzinfo=ZoneInfo("UTC")))

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert actual[0].incomes == 0
    assert actual[0].expenses == 0
    assert actual[0].balance == 0
    assert actual[0].have == 5
    assert actual[0].delta == 5


def test_account_worth_post_save_new():
    AccountBalanceFactory()

    actual = AccountBalance.objects.first()
    assert actual.have == 20

    AccountWorthFactory(price=5)

    actual = AccountBalance.objects.first()
    assert actual.have == 5


# SavingWorth
def test_saving_worth_str():
    model = SavingWorthFactory()

    assert str(model) == "1999-01-01 02:03 - Savings"


def test_saving_worth_post_save():
    SavingWorthFactory()

    assert SavingBalance.objects.count() == 2

    actual = SavingBalance.objects.first()
    assert actual.saving_type.title == "Savings"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0
    assert actual.market_value == 5


def test_saving_worth_post_save_new():
    SavingFactory(price=20, fee=5)

    actual = SavingBalance.objects.first()
    assert actual.saving_type.title == "Savings"
    assert actual.fee == 5
    assert actual.incomes == 20
    assert actual.market_value == 0

    SavingWorthFactory(price=30)

    assert SavingBalance.objects.count() == 2

    actual = SavingBalance.objects.first()
    assert actual.saving_type.title == "Savings"
    assert actual.fee == 5
    assert actual.incomes == 20
    assert actual.market_value == 30


# PensionWorth
def test_pension_worth_str():
    model = PensionWorthFactory()

    assert str(model) == "1999-01-01 02:03 - PensionType"


def test_pension_worth_post_save():
    PensionWorthFactory()

    assert PensionBalance.objects.count() == 2

    actual = PensionBalance.objects.first()
    assert actual.pension_type.title == "PensionType"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0
    assert actual.market_value == 5


def test_pension_worth_post_save_new():
    PensionBalanceFactory()

    actual = PensionBalance.objects.first()
    assert actual.pension_type.title == "PensionType"
    assert actual.market_value == 25

    PensionWorthFactory(price=3)

    assert PensionBalance.objects.count() == 2

    actual = PensionBalance.objects.first()
    assert actual.pension_type.title == "PensionType"
    assert actual.market_value == 3


WORTH_FACTORIES = [AccountWorthFactory, SavingWorthFactory, PensionWorthFactory]


@pytest.mark.parametrize(
    "service, factory, field, fund_factory",
    [
        (AccountWorthModelService, AccountWorthFactory, "account", AccountFactory),
        (SavingWorthModelService, SavingWorthFactory, "saving_type", SavingTypeFactory),
        (
            PensionWorthModelService,
            PensionWorthFactory,
            "pension_type",
            PensionTypeFactory,
        ),
    ],
)
def test_worth_objects_are_the_users_journals(
    main_user, second_user, service, factory, field, fund_factory
):
    mine = fund_factory(title="Mine")
    factory(**{field: mine})
    factory(**{field: fund_factory(title="Theirs", journal=second_user.journal)})

    actual = service(main_user).objects

    assert [getattr(worth, field) for worth in actual] == [mine]


# the account row's two 2000 worths share a day, so the later time is the latest
@pytest.mark.parametrize(
    "service, factory, first_2000, last_2000",
    [
        (
            AccountWorthModelService,
            AccountWorthFactory,
            dt(2000, 12, 31, 1, 1, 1, tzinfo=ZoneInfo("UTC")),
            dt(2000, 12, 31, 3, 2, 1, tzinfo=ZoneInfo("UTC")),
        ),
        (
            SavingWorthModelService,
            SavingWorthFactory,
            dt(2000, 1, 1, tzinfo=ZoneInfo("UTC")),
            dt(2000, 12, 31, tzinfo=ZoneInfo("UTC")),
        ),
        (
            PensionWorthModelService,
            PensionWorthFactory,
            dt(2000, 1, 1, tzinfo=ZoneInfo("UTC")),
            dt(2000, 12, 31, tzinfo=ZoneInfo("UTC")),
        ),
    ],
)
def test_worth_have_is_each_years_latest_worth(
    main_user, service, factory, first_2000, last_2000
):
    factory(date=dt(1970, 1, 1, tzinfo=ZoneInfo("UTC")), price=1)
    factory(date=dt(1970, 12, 31, tzinfo=ZoneInfo("UTC")), price=2)
    factory(date=first_2000, price=3)
    factory(date=last_2000, price=4)

    actual = service(main_user).have()

    assert [(x["year"], x["category_id"], x["have"]) for x in actual] == [
        (1970, 1, 2),
        (2000, 1, 4),
    ]


@pytest.mark.parametrize(
    "service",
    [AccountWorthModelService, SavingWorthModelService, PensionWorthModelService],
)
def test_worth_have_of_a_journal_with_no_worth_is_empty(main_user, service):
    assert service(main_user).have() == []


@pytest.mark.parametrize("factory", WORTH_FACTORIES)
def test_worth_price_is_never_null(factory):
    with pytest.raises(IntegrityError), transaction.atomic():
        factory(price=None)


@pytest.mark.parametrize("factory", WORTH_FACTORIES)
def test_worth_price_is_required(factory):
    worth = factory.build(price=None)

    with pytest.raises(ValidationError):
        worth._meta.get_field("price").clean(None, worth)


@pytest.mark.parametrize(
    "factory, field, fund_factory",
    [
        (AccountWorthFactory, "account", AccountFactory),
        (SavingWorthFactory, "saving_type", SavingTypeFactory),
        (PensionWorthFactory, "pension_type", PensionTypeFactory),
    ],
)
def test_worth_journal_is_its_funds(second_user, factory, field, fund_factory):
    journal = second_user.journal

    obj = factory.build(**{field: fund_factory(journal=journal)})

    assert obj.journal == journal
