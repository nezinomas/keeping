from datetime import date
from typing import NamedTuple

import pytest

from ...accounts.services.model_services import (
    AccountBalanceModelService,
)
from ...accounts.tests.factories import AccountBalance, AccountFactory
from ...core.tests.utils import count_queries
from ...expenses.tests.factories import ExpenseFactory
from ...incomes.tests.factories import IncomeFactory
from ...savings.models import SavingBalance
from ...savings.services.model_services import SavingBalanceModelService
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ..services.model_services import (
    SavingCloseModelService,
    TransactionModelService,
)
from .factories import SavingCloseFactory, TransactionFactory
from .kinds import FUND_MOVES, KINDS, by_kind

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


class AccountRow(NamedTuple):
    title: str
    year: int
    past: int
    incomes: int
    expenses: int
    balance: int
    delta: int


class FundRow(NamedTuple):
    title: str
    year: int
    past_amount: int
    past_fee: int
    fee: int
    incomes: int


# what a 0,01 move from "From" to "To" in 1999 leaves; the sync writes each
# balance up to a year past the last record
MOVES_OF_ONE_CENT = [
    pytest.param(
        KINDS["transaction"],
        [
            AccountRow("From", 1999, 0, 0, 1, -1, 1),
            AccountRow("From", 2000, -1, 0, 0, -1, 1),
            AccountRow("To", 1999, 0, 1, 0, 1, -1),
            AccountRow("To", 2000, 1, 0, 0, 1, -1),
        ],
        [],
        id="transaction",
    ),
    pytest.param(
        KINDS["sale"],
        [
            AccountRow("To", 1999, 0, 1, 0, 1, -1),
            AccountRow("To", 2000, 1, 0, 0, 1, -1),
        ],
        [FundRow("From", 1999, 0, 0, 0, 0), FundRow("From", 2000, 0, 0, 0, 0)],
        id="sale",
    ),
    pytest.param(
        KINDS["switch"],
        [],
        [
            FundRow("From", 1999, 0, 0, 0, 0),
            FundRow("From", 2000, 0, 0, 0, 0),
            FundRow("To", 1999, 0, 0, 0, 1),
            FundRow("To", 2000, 1, 0, 0, 1),
        ],
        id="switch",
    ),
]


def account_rows(user):
    return [
        AccountRow(
            row.account.title,
            row.year,
            row.past,
            row.incomes,
            row.expenses,
            row.balance,
            row.delta,
        )
        for row in AccountBalanceModelService(user)
        .items()
        .order_by("account__title", "year")
    ]


def fund_rows(user):
    return [
        FundRow(
            row.saving_type.title,
            row.year,
            row.past_amount,
            row.past_fee,
            row.fee,
            row.incomes,
        )
        for row in SavingBalanceModelService(user)
        .items()
        .order_by("saving_type__title", "year")
    ]


def reloaded(move):
    # a fund move settles what it leaves only when loaded from the database
    return type(move).objects.get(pk=move.pk)


@by_kind
def test_related(main_user, second_user, kind):
    mine_from = kind.from_factory(title="F1")
    mine_to = kind.to_factory(title="T1")
    their_from = kind.from_factory(title="F2", journal=second_user.journal)
    their_to = kind.to_factory(title="T2", journal=second_user.journal)

    kind.factory(to_account=mine_to, from_account=mine_from)
    kind.factory(to_account=their_to, from_account=their_from)

    actual = kind.service(main_user).objects

    assert len(actual) == 1
    assert str(actual[0].from_account) == "F1"
    assert str(actual[0].to_account) == "T1"


def test_transaction_year(main_user, second_user):
    a = AccountFactory(title="T1", journal=second_user.journal)

    TransactionFactory(date=date(1999, 1, 1))
    TransactionFactory(date=date(2000, 1, 1))
    TransactionFactory(date=date(2000, 1, 1), from_account=a)

    actual = TransactionModelService(main_user).year(1999)

    assert actual.count() == 1


@by_kind
def test_items_read_both_ends_in_as_many_queries_for_2_as_for_6(main_user, kind):
    def ends():
        return [
            (move.from_account.title, move.to_account.title)
            for move in kind.service(main_user).items()
        ]

    kind.factory.create_batch(2)
    two = count_queries(ends)
    kind.factory.create_batch(4)

    assert len(ends()) == 6
    assert count_queries(ends) == two


def accounts_with_a_past():
    ends = AccountFactory(title="From"), AccountFactory(title="To")
    IncomeFactory(account=ends[0], date=date(1998, 1, 1), price=6)
    ExpenseFactory(account=ends[0], date=date(1998, 1, 1), price=5)
    IncomeFactory(account=ends[1], date=date(1998, 1, 1), price=5)
    ExpenseFactory(account=ends[1], date=date(1998, 1, 1), price=3)
    return ends


def fund_with_a_past(title, price, payer):
    fund = SavingTypeFactory(title=title)
    SavingFactory(
        saving_type=fund, account=payer, price=price, date=date(1998, 1, 1), fee=2
    )
    return fund


def a_fund_and_an_account_with_a_past():
    account = AccountFactory(title="To")
    IncomeFactory(account=account, price=10, date=date(1998, 1, 1))
    return fund_with_a_past("From", 40, AccountFactory(title="Payer")), account


def funds_with_a_past():
    payer = AccountFactory(title="Payer")
    return fund_with_a_past("From", 40, payer), fund_with_a_past("To", 50, payer)


TRANSACTION_ACCOUNTS = [
    AccountRow("From", 1998, 0, 6, 5, 1, -1),
    AccountRow("From", 1999, 1, 0, 1, 0, 0),
    AccountRow("From", 2000, 0, 0, 0, 0, 0),
    AccountRow("To", 1998, 0, 5, 3, 2, -2),
    AccountRow("To", 1999, 2, 1, 0, 3, -3),
    AccountRow("To", 2000, 3, 0, 0, 3, -3),
]
SALE_ACCOUNTS = [
    AccountRow("Payer", 1998, 0, 0, 40, -40, 40),
    AccountRow("Payer", 1999, -40, 0, 0, -40, 40),
    AccountRow("Payer", 2000, -40, 0, 0, -40, 40),
    AccountRow("To", 1998, 0, 10, 0, 10, -10),
    AccountRow("To", 1999, 10, 1, 0, 11, -11),
    AccountRow("To", 2000, 11, 0, 0, 11, -11),
]
SALE_FUNDS = [
    FundRow("From", 1998, 0, 0, 2, 40),
    FundRow("From", 1999, 40, 2, 2, 40),
    FundRow("From", 2000, 40, 2, 2, 40),
]
SWITCH_FUNDS = [
    *SALE_FUNDS,
    FundRow("To", 1998, 0, 0, 2, 50),
    FundRow("To", 1999, 50, 2, 2, 51),
    FundRow("To", 2000, 51, 2, 2, 51),
]


def kept_and_emptied(name, ends_with_a_past, accounts, funds):
    return [
        pytest.param(
            KINDS[name],
            ends_with_a_past,
            accounts,
            funds,
            emptied,
            id=f"{name}-{state}",
        )
        for emptied, state in [(False, "kept"), (True, "emptied")]
    ]


@pytest.mark.parametrize(
    "kind, ends_with_a_past, accounts, funds, balances_emptied",
    [
        *kept_and_emptied(
            "transaction", accounts_with_a_past, TRANSACTION_ACCOUNTS, []
        ),
        *kept_and_emptied(
            "sale", a_fund_and_an_account_with_a_past, SALE_ACCOUNTS, SALE_FUNDS
        ),
        # a switch syncs no account: Payer keeps what its savings wrote, or none
        pytest.param(
            KINDS["switch"],
            funds_with_a_past,
            [
                AccountRow("Payer", 1998, 0, 0, 90, -90, 90),
                AccountRow("Payer", 1999, -90, 0, 0, -90, 90),
            ],
            SWITCH_FUNDS,
            False,
            id="switch-kept",
        ),
        pytest.param(
            KINDS["switch"],
            funds_with_a_past,
            [],
            SWITCH_FUNDS,
            True,
            id="switch-emptied",
        ),
    ],
)
@pytest.mark.syncs
def test_save_carries_each_ends_past(
    main_user, kind, ends_with_a_past, accounts, funds, balances_emptied
):
    from_account, to_account = ends_with_a_past()

    if balances_emptied:
        AccountBalance.objects.all().delete()
        SavingBalance.objects.all().delete()

    kind.factory(
        date=date(1999, 1, 1), from_account=from_account, to_account=to_account, price=1
    )

    assert account_rows(main_user) == accounts
    assert fund_rows(main_user) == funds


def from_and_to(kind):
    return {
        "from_account": kind.from_factory(title="From"),
        "to_account": kind.to_factory(title="To"),
    }


def new_price(kind):
    move = reloaded(kind.factory(price=5, **from_and_to(kind)))
    move.price = 1
    move.save()
    return [move]


def nothing_changed(kind):
    move = kind.factory(price=1, **from_and_to(kind))
    reloaded(move).save()
    return [move]


def new_ends(kind):
    move = reloaded(
        kind.factory(
            from_account=kind.from_factory(title="Old-From"),
            to_account=kind.to_factory(title="Old-To"),
            price=1,
        )
    )
    move.from_account = kind.from_factory(title="From")
    move.to_account = kind.to_factory(title="To")
    move.save()
    return [move]


def another_deleted(kind):
    ends = from_and_to(kind)
    kept = kind.factory(price=1, **ends)
    reloaded(kind.factory(price=5, **ends)).delete()
    return [kept]


@pytest.mark.parametrize(
    "edit",
    [
        pytest.param(new_price, id="new-price"),
        pytest.param(nothing_changed, id="nothing-changed"),
        pytest.param(new_ends, id="new-ends"),
        pytest.param(another_deleted, id="another-deleted"),
    ],
)
@pytest.mark.parametrize("kind, accounts, funds", MOVES_OF_ONE_CENT)
@pytest.mark.syncs
def test_an_edit_leaves_the_balances_of_one_cent(
    main_user, kind, accounts, funds, edit
):
    left = edit(kind)

    assert account_rows(main_user) == accounts
    assert fund_rows(main_user) == funds
    assert list(kind.model.objects.all()) == left


@by_kind
@pytest.mark.syncs
def test_delete_drops_its_balances(main_user, kind):
    move = kind.factory(**from_and_to(kind))

    reloaded(move).delete()

    assert account_rows(main_user) == []
    assert fund_rows(main_user) == []
    assert not type(move).objects.exists()


@pytest.mark.parametrize(
    "kind, sums_of, with_fee, sums",
    [
        pytest.param(
            KINDS["transaction"],
            KINDS["transaction"].service.expenses,
            {},
            [(1970, {"expenses": 25}, "From"), (1999, {"expenses": 30}, "From")],
            id="transaction-expenses",
        ),
        *[
            pytest.param(
                kind,
                kind.service.expenses,
                {"fee": 1},
                [
                    (1970, {"expenses": 25, "fee": 1}, "From"),
                    (1999, {"expenses": 30, "fee": 3}, "From"),
                ],
                id=f"{name}-expenses",
            )
            for name, kind in FUND_MOVES.items()
        ],
        pytest.param(
            KINDS["transaction"],
            KINDS["transaction"].service.incomes,
            {},
            [
                (1970, {"incomes": 25}, "To1"),
                (1999, {"incomes": 29}, "To1"),
                (1999, {"incomes": 1}, "To2"),
            ],
            id="transaction-incomes",
        ),
    ],
)
def test_sums_each_end_by_year(main_user, kind, sums_of, with_fee, sums):
    ends = {
        "From": kind.from_factory(title="From"),
        "To1": kind.to_factory(title="To1"),
        "To2": kind.to_factory(title="To2"),
    }
    sent = {"from_account": ends["From"], **with_fee}
    kind.factory(date=date(1999, 1, 1), price=25, to_account=ends["To1"], **sent)
    kind.factory(date=date(1999, 6, 1), price=4, to_account=ends["To1"], **sent)
    kind.factory(date=date(1999, 1, 1), price=1, to_account=ends["To2"], **sent)
    kind.factory(date=date(1970, 1, 1), price=25, to_account=ends["To1"], **sent)

    actual = sums_of(kind.service(main_user))

    assert list(actual) == [
        {"year": year, **sum_, "category_id": ends[end].pk} for year, sum_, end in sums
    ]


def test_str_names_the_day_both_ends_and_the_grouped_price():
    move = TransactionFactory.build(
        date=date(2001, 2, 3),
        price=123456,
        from_account=AccountFactory.build(title="Ex. Fund"),
        to_account=AccountFactory.build(title="Ex. Bank"),
    )

    assert str(move) == "2001-02-03 Ex. Fund -> Ex. Bank: 1.234,56"


@pytest.mark.parametrize(
    "month, sums",
    [
        pytest.param(0, [(date(1999, 1, 1), 25), (date(1999, 2, 1), 1)], id="year"),
        pytest.param(2, [(date(1999, 2, 1), 1)], id="february"),
    ],
)
def test_saving_close_month_sums(main_user, month, sums):
    SavingCloseFactory(date=date(1999, 1, 1), price=25)
    SavingCloseFactory(date=date(1999, 2, 1), price=1)
    SavingCloseFactory(date=date(1970, 2, 1), price=7)

    actual = SavingCloseModelService(main_user).sum_by_month(1999, month)

    assert list(actual) == [
        {"date": day, "sum": sum_, "title": "savings_close"} for day, sum_ in sums
    ]


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(KINDS["transaction"], id="transaction"),
        pytest.param(KINDS["sale"], id="sale"),
    ],
)
def test_move_journal_is_its_from_accounts(second_user, kind):
    journal = second_user.journal

    obj = kind.factory.build(from_account=kind.from_factory(journal=journal))

    assert obj.journal == journal
