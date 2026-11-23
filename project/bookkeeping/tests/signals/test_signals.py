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
from ....pensions.models import PensionBalance
from ....pensions.services.model_services import PensionBalanceModelService
from ....pensions.tests.factories import (
    PensionBalanceFactory,
    PensionFactory,
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


ACCOUNT_WRITTEN = ACCOUNT_VALUES | {
    "incomes": 2000,
    "expenses": 1000,
    "have": 1000,
    "balance": 1000,
}


def _as_stored(values):
    stored = dict(values)
    if values["latest_check"]:
        stored["latest_check"] = timezone.make_aware(values["latest_check"])
    return stored


@pytest.mark.parametrize(
    "kind, stored_years, years, values",
    [
        pytest.param(
            "account", (), (2023,), ACCOUNT_VALUES, id="account_into_an_empty_table"
        ),
        pytest.param(
            "saving", (), (2023,), SAVING_VALUES, id="saving_into_an_empty_table"
        ),
        pytest.param(
            "pension", (), (2023,), SAVING_VALUES, id="pension_into_an_empty_table"
        ),
        pytest.param(
            "account",
            (),
            (2023,),
            ACCOUNT_VALUES | {"latest_check": None},
            id="account_with_no_check",
        ),
        pytest.param(
            "account",
            (1999,),
            (2024,),
            ACCOUNT_WRITTEN | {"latest_check": datetime(2024, 1, 1)},
            id="account_new_year",
        ),
        pytest.param(
            "account",
            (1999,),
            (1999,),
            ACCOUNT_WRITTEN
            | {"latest_check": datetime(2023, 1, 2), "past": 1, "delta": 1},
            id="account_same_year",
        ),
        pytest.param(
            "account",
            (1999, 2000),
            (2000, 2001),
            ACCOUNT_WRITTEN | {"latest_check": datetime(2024, 1, 1)},
            id="account_drops_updates_and_adds_years",
        ),
        pytest.param("saving", (1999,), (2023,), SAVING_VALUES, id="saving_new_year"),
        pytest.param("saving", (1999,), (1999,), SAVING_VALUES, id="saving_same_year"),
        pytest.param("pension", (1999,), (2023,), SAVING_VALUES, id="pension_new_year"),
        pytest.param(
            "pension", (1999,), (1999,), SAVING_VALUES, id="pension_same_year"
        ),
    ],
)
def test_sync_writes_the_frame_as_the_stored_rows(
    main_user, kind, stored_years, years, values
):
    balances = BALANCES[kind]
    owner = balances.owner_factory()
    for stored_year in stored_years:
        balances.factory(**{balances.owner_field: owner, "year": stored_year})
    rows = {(owner.pk, year): values for year in years}

    BalanceSynchronizer(balances.service, main_user, _frame(rows, rows))

    assert _balance_rows(kind, main_user) == {key: _as_stored(values) for key in rows}


@pytest.mark.parametrize(
    "kept", [[(0, 2000), (1, 1999)], []], ids=["some_rows", "no_row"]
)
@pytest.mark.parametrize("kind", BALANCES)
def test_sync_deletes_the_rows_the_frame_drops(main_user, kind, kept):
    owners = _owners_with_balances(kind, 2)
    keep = {(owners[i].pk, year) for i, year in kept}
    before = _balance_rows(kind, main_user)

    BalanceSynchronizer(BALANCES[kind].service, main_user, _frame(before, keep))

    assert _balance_rows(kind, main_user) == {key: before[key] for key in keep}


def _deleting(kind, user, owners):
    return _frame(_balance_rows(kind, user), {(owner.pk, 2000) for owner in owners})


def _inserting_into_an_empty_table(kind, user, owners):
    BALANCES[kind].service(user).objects.all().delete()
    rows = {(owner.pk, 2023): INSERT_VALUES[kind] for owner in owners}
    return _frame(rows, rows)


def _updating(kind, user, owners):
    rows = {key: INSERT_VALUES[kind] for key in _balance_rows(kind, user)}
    return _frame(rows, rows)


@pytest.mark.parametrize(
    "frame_of",
    [_deleting, _inserting_into_an_empty_table, _updating],
    ids=["delete", "insert", "update"],
)
@pytest.mark.parametrize("kind", BALANCES)
def test_sync_query_count_does_not_grow(main_user, kind, frame_of):
    service = BALANCES[kind].service

    def queries_syncing(count):
        service(main_user).objects.all().delete()
        frame = frame_of(kind, main_user, _owners_with_balances(kind, count))
        return count_queries(lambda: BalanceSynchronizer(service, main_user, frame))

    assert queries_syncing(2) == queries_syncing(6)


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


@pytest.mark.parametrize(
    "owner_factory, entry_factory, balance_model, owner_field",
    [
        (AccountFactory, IncomeFactory, AccountBalance, "account"),
        (PensionTypeFactory, PensionFactory, PensionBalance, "pension_type"),
    ],
    ids=["account", "pension"],
)
def test_closing_and_reopening_an_owner_resyncs_its_years(
    owner_factory, entry_factory, balance_model, owner_field
):
    owner = owner_factory(title="SEB")
    entry_factory(price=100, date=date(1999, 1, 1), **{owner_field: owner})
    # another owner's row carries the journal's years on to 2002
    other = owner_factory(title="IB")
    entry_factory(price=50, date=date(2001, 1, 1), **{owner_field: other})
    assert _years(balance_model, **{owner_field: owner}) == [1999, 2000, 2001, 2002]

    owner.closed = 1999
    owner.save()
    assert _years(balance_model, **{owner_field: owner}) == [1999]

    owner.closed = None
    owner.save()
    assert _years(balance_model, **{owner_field: owner}) == [1999, 2000, 2001, 2002]
