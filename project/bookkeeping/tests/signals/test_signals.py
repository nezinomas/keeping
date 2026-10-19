from datetime import date, datetime
from typing import NamedTuple

import polars as pl
import pytest
from django.utils import timezone

from ....accounts.services.model_services import AccountBalanceModelService
from ....accounts.tests.factories import (
    AccountBalance,
    AccountBalanceFactory,
    AccountFactory,
)
from ....core.lib.db_sync import ACCOUNT_FIELDS, SAVING_FIELDS, BalanceSynchronizer
from ....core.tests.utils import count_queries
from ....incomes.tests.factories import IncomeFactory
from ....pensions.services.model_services import PensionBalanceModelService
from ....pensions.tests.factories import (
    PensionBalanceFactory,
    PensionTypeFactory,
)
from ....savings.services.model_services import SavingBalanceModelService
from ....savings.tests.factories import (
    SavingBalance,
    SavingBalanceFactory,
    SavingFactory,
    SavingTypeFactory,
)
from ...tests.factories import AccountWorthFactory, SavingWorthFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "existing_years, columns, expect",
    [
        (
            [2023, 2022],
            {
                "year": [2023, 2024],
                "incomes": [2000, 3000],
                "expenses": [1000, 1500],
                "have": [1000, 1500],
                "latest_check": [datetime(2023, 1, 2), datetime(2024, 1, 1)],
                "balance": [1000, 1500],
                "past": [1, 0],
                "delta": [1, 0],
            },
            [
                (2023, 2000, timezone.make_aware(datetime(2023, 1, 2))),
                (2024, 3000, timezone.make_aware(datetime(2024, 1, 1))),
            ],
        ),
        (
            [],
            {
                "year": [2023],
                "incomes": [1000],
                "expenses": [500],
                "have": [500],
                "latest_check": [None],
                "balance": [500],
                "past": [0],
                "delta": [0],
            },
            [(2023, 1000, None)],
        ),
    ],
    ids=["mixed_operations", "null_latest_check"],
)
def test_sync_writes_the_account_frame(main_user, existing_years, columns, expect):
    account = AccountFactory()
    for year in existing_years:
        AccountBalanceFactory(year=year, account=account)
    df = pl.DataFrame(
        {"category_id": [account.pk] * len(columns["year"]), **columns}
    ).lazy()

    BalanceSynchronizer(AccountBalanceModelService, main_user, df)

    actual = AccountBalance.objects.order_by("year")
    assert [(r.year, r.incomes, r.latest_check) for r in actual] == expect


class Balances(NamedTuple):
    service: type
    factory: type
    owner_factory: type
    owner_field: str
    fields: list


BALANCES = {
    "account": Balances(
        AccountBalanceModelService,
        AccountBalanceFactory,
        AccountFactory,
        "account",
        ACCOUNT_FIELDS,
    ),
    "saving": Balances(
        SavingBalanceModelService,
        SavingBalanceFactory,
        SavingTypeFactory,
        "saving_type",
        SAVING_FIELDS,
    ),
    "pension": Balances(
        PensionBalanceModelService,
        PensionBalanceFactory,
        PensionTypeFactory,
        "pension_type",
        SAVING_FIELDS,
    ),
}


def _owners_with_balances(kind, count):
    balances = BALANCES[kind]
    owners = [balances.owner_factory(title=f"Owner {i}") for i in range(count)]
    for owner in owners:
        for year in (1999, 2000):
            balances.factory(**{balances.owner_field: owner, "year": year})
    return owners


def _balance_rows(kind, user):
    balances = BALANCES[kind]
    owner_id = f"{balances.owner_field}_id"
    rows = balances.service(user).objects.values(owner_id, "year", *balances.fields)
    return {(row.pop(owner_id), row.pop("year")): row for row in rows}


def _frame(rows, keep):
    return pl.DataFrame(
        [{"category_id": key[0], "year": key[1], **rows[key]} for key in keep]
    ).lazy()


ACCOUNT_VALUES = {
    "incomes": 1000,
    "expenses": 500,
    "have": 500,
    "latest_check": datetime(2023, 1, 1),
    "balance": 500,
    "past": 0,
    "delta": 0,
}

SAVING_VALUES = {
    "latest_check": datetime(2023, 1, 1),
    "past_amount": 10,
    "past_fee": 20,
    "fee": 30,
    "per_year_incomes": 40,
    "per_year_fee": 50,
    "sold": 60,
    "sold_fee": 70,
    "incomes": 80,
    "market_value": 90,
    "profit_sum": 100,
    "profit_proc": 110,
    "sold_since_check": 0,
}

INSERT_VALUES = {
    "account": ACCOUNT_VALUES,
    "saving": SAVING_VALUES,
    "pension": SAVING_VALUES,
}


def _empty_frame(kind):
    columns = ["category_id", "year", *BALANCES[kind].fields]
    return pl.DataFrame({column: [] for column in columns}).lazy()


@pytest.mark.parametrize("kind", BALANCES)
def test_sync_inserts_a_row_into_an_empty_db(main_user, kind):
    owner = BALANCES[kind].owner_factory()
    values = INSERT_VALUES[kind]
    frame = _frame({(owner.pk, 2023): values}, [(owner.pk, 2023)])

    BalanceSynchronizer(BALANCES[kind].service, main_user, frame)

    assert _balance_rows(kind, main_user) == {
        (owner.pk, 2023): values
        | {"latest_check": timezone.make_aware(datetime(2023, 1, 1))}
    }


ACCOUNT_WRITTEN = ACCOUNT_VALUES | {
    "incomes": 2000,
    "expenses": 1000,
    "have": 1000,
    "balance": 1000,
}


@pytest.mark.parametrize(
    "kind, year, values",
    [
        pytest.param(
            "account",
            2024,
            ACCOUNT_WRITTEN | {"latest_check": datetime(2024, 1, 1)},
            id="account_new_year",
        ),
        pytest.param(
            "account",
            1999,
            ACCOUNT_WRITTEN
            | {"latest_check": datetime(2023, 1, 2), "past": 1, "delta": 1},
            id="account_same_year",
        ),
        pytest.param("saving", 2023, SAVING_VALUES, id="saving_new_year"),
        pytest.param("saving", 1999, SAVING_VALUES, id="saving_same_year"),
        pytest.param("pension", 2023, SAVING_VALUES, id="pension_new_year"),
        pytest.param("pension", 1999, SAVING_VALUES, id="pension_same_year"),
    ],
)
def test_sync_writes_the_frame_over_the_1999_row(main_user, kind, year, values):
    balances = BALANCES[kind]
    owner = balances.owner_factory()
    balances.factory(**{balances.owner_field: owner, "year": 1999})
    frame = _frame({(owner.pk, year): values}, [(owner.pk, year)])

    BalanceSynchronizer(balances.service, main_user, frame)

    assert _balance_rows(kind, main_user) == {
        (owner.pk, year): values
        | {"latest_check": timezone.make_aware(values["latest_check"])}
    }


@pytest.mark.parametrize("years", [(1999,), (2023, 2024)], ids=["one_row", "two_rows"])
@pytest.mark.parametrize("kind", BALANCES)
def test_sync_empty_frame_deletes_every_row(main_user, kind, years):
    for year in years:
        BALANCES[kind].factory(year=year)

    BalanceSynchronizer(BALANCES[kind].service, main_user, _empty_frame(kind))

    assert _balance_rows(kind, main_user) == {}


@pytest.mark.parametrize("kind", BALANCES)
def test_sync_deletes_only_the_rows_it_drops(main_user, kind):
    a, b = _owners_with_balances(kind, 2)
    keep = {(a.pk, 2000), (b.pk, 1999)}
    before = _balance_rows(kind, main_user)

    BalanceSynchronizer(BALANCES[kind].service, main_user, _frame(before, keep))

    assert _balance_rows(kind, main_user) == {key: before[key] for key in keep}


@pytest.mark.parametrize("kind", BALANCES)
def test_sync_delete_query_count_does_not_grow(main_user, kind):
    service = BALANCES[kind].service

    def queries_deleting(count):
        service(main_user).objects.all().delete()
        keep = {(owner.pk, 2000) for owner in _owners_with_balances(kind, count)}
        frame = _frame(_balance_rows(kind, main_user), keep)
        return count_queries(lambda: BalanceSynchronizer(service, main_user, frame))

    assert queries_deleting(2) == queries_deleting(6)


def _years(model, **owner):
    return sorted(model.objects.filter(**owner).values_list("year", flat=True))


def test_moving_the_last_purchase_back_a_year_drops_the_old_next_year():
    account = AccountFactory(title="IB")
    saving_type = SavingTypeFactory(title="VALL")
    saving = SavingFactory(
        account=account, saving_type=saving_type, date=date(2027, 1, 1)
    )
    assert _years(AccountBalance, account=account) == [2027, 2028]
    assert _years(SavingBalance, saving_type=saving_type) == [2027, 2028]

    saving.date = date(2026, 1, 1)
    saving.save()

    assert _years(AccountBalance, account=account) == [2026, 2027]
    assert _years(SavingBalance, saving_type=saving_type) == [2026, 2027]


def test_removing_the_latest_year_keeps_every_other_owners_rows():
    seb = AccountFactory(title="SEB")
    ib = AccountFactory(title="IB")
    IncomeFactory(account=seb, price=100, date=date(1999, 1, 1))
    later = IncomeFactory(account=ib, price=50, date=date(2000, 1, 1))
    assert _years(AccountBalance, account=seb) == [1999, 2000, 2001]

    later.delete()

    assert _years(AccountBalance, account=seb) == [1999, 2000]
    assert _years(AccountBalance, account=ib) == []
    assert AccountBalance.objects.get(account=seb, year=2000).balance == 100


@pytest.mark.parametrize(
    "owner_factory, entry_factory, worth_factory, balance_model, owner_field",
    [
        (
            SavingTypeFactory,
            SavingFactory,
            SavingWorthFactory,
            SavingBalance,
            "saving_type",
        ),
        (AccountFactory, IncomeFactory, AccountWorthFactory, AccountBalance, "account"),
    ],
    ids=["fund", "account"],
)
def test_a_first_worth_equal_to_the_stored_amount_stores_its_check(
    owner_factory, entry_factory, worth_factory, balance_model, owner_field
):
    owner = {owner_field: owner_factory()}
    entry_factory(price=100, **owner)

    # with no worth yet the stored amount is 0, so a worth of 0 changes only the check
    worth = worth_factory(price=0, **owner)

    assert balance_model.objects.get(year=1999, **owner).latest_check == worth.date


def test_closing_and_reopening_an_account_resyncs_its_years():
    seb = AccountFactory(title="SEB")
    IncomeFactory(account=seb, price=100, date=date(1999, 1, 1))
    # another account's row carries the journal's years on to 2002
    IncomeFactory(account=AccountFactory(title="IB"), price=50, date=date(2001, 1, 1))
    assert _years(AccountBalance, account=seb) == [1999, 2000, 2001, 2002]

    seb.closed = 1999
    seb.save()
    assert _years(AccountBalance, account=seb) == [1999]

    seb.closed = None
    seb.save()
    assert _years(AccountBalance, account=seb) == [1999, 2000, 2001, 2002]
