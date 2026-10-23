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
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)
from .factories import SavingChangeFactory, SavingCloseFactory, TransactionFactory

pytestmark = pytest.mark.django_db


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


MOVES = [
    pytest.param(TransactionFactory, AccountFactory, AccountFactory, id="transaction"),
    pytest.param(
        SavingCloseFactory, SavingTypeFactory, AccountFactory, id="saving_close"
    ),
    pytest.param(
        SavingChangeFactory, SavingTypeFactory, SavingTypeFactory, id="saving_change"
    ),
]

# what a 0,01 move from "From" to "To" in 1999 leaves; the sync writes each
# balance up to a year past the last record
MOVES_OF_ONE_CENT = [
    pytest.param(
        TransactionFactory,
        AccountFactory,
        AccountFactory,
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
        SavingCloseFactory,
        SavingTypeFactory,
        AccountFactory,
        [
            AccountRow("To", 1999, 0, 1, 0, 1, -1),
            AccountRow("To", 2000, 1, 0, 0, 1, -1),
        ],
        [FundRow("From", 1999, 0, 0, 0, 0), FundRow("From", 2000, 0, 0, 0, 0)],
        id="saving_close",
    ),
    pytest.param(
        SavingChangeFactory,
        SavingTypeFactory,
        SavingTypeFactory,
        [],
        [
            FundRow("From", 1999, 0, 0, 0, 0),
            FundRow("From", 2000, 0, 0, 0, 0),
            FundRow("To", 1999, 0, 0, 0, 1),
            FundRow("To", 2000, 1, 0, 0, 1),
        ],
        id="saving_change",
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


@pytest.mark.parametrize(
    "service, factory, from_factory, to_factory, from_title, to_title",
    [
        pytest.param(
            TransactionModelService,
            TransactionFactory,
            AccountFactory,
            AccountFactory,
            "F1",
            "T1",
            id="transaction",
        ),
        pytest.param(
            SavingCloseModelService,
            SavingCloseFactory,
            SavingTypeFactory,
            AccountFactory,
            "S1",
            "A1",
            id="saving_close",
        ),
        pytest.param(
            SavingChangeModelService,
            SavingChangeFactory,
            SavingTypeFactory,
            SavingTypeFactory,
            "F1",
            "T1",
            id="saving_change",
        ),
    ],
)
def test_related(
    main_user,
    second_user,
    service,
    factory,
    from_factory,
    to_factory,
    from_title,
    to_title,
):
    mine_from = from_factory(title=from_title)
    mine_to = to_factory(title=to_title)
    their_from = from_factory(title="F2", journal=second_user.journal)
    their_to = to_factory(title="T2", journal=second_user.journal)

    factory(to_account=mine_to, from_account=mine_from)
    factory(to_account=their_to, from_account=their_from)

    actual = service(main_user).objects

    assert len(actual) == 1
    assert str(actual[0].from_account) == from_title
    assert str(actual[0].to_account) == to_title


def test_transaction_year(main_user, second_user):
    a = AccountFactory(title="T1", journal=second_user.journal)

    TransactionFactory(date=date(1999, 1, 1))
    TransactionFactory(date=date(2000, 1, 1))
    TransactionFactory(date=date(2000, 1, 1), from_account=a)

    actual = TransactionModelService(main_user).year(1999)

    assert actual.count() == 1


@pytest.mark.parametrize(
    "service, factory",
    [
        pytest.param(TransactionModelService, TransactionFactory, id="transaction"),
        pytest.param(SavingCloseModelService, SavingCloseFactory, id="saving_close"),
        pytest.param(SavingChangeModelService, SavingChangeFactory, id="saving_change"),
    ],
)
def test_items_read_both_ends_in_as_many_queries_for_2_as_for_6(
    main_user, service, factory
):
    def ends():
        return [
            (move.from_account.title, move.to_account.title)
            for move in service(main_user).items()
        ]

    factory.create_batch(2)
    two = count_queries(ends)
    factory.create_batch(4)

    assert len(ends()) == 6
    assert count_queries(ends) == two


@pytest.mark.parametrize("balances_emptied", [False, True], ids=["kept", "emptied"])
def test_transaction_save_carries_each_accounts_past(main_user, balances_emptied):
    a_from = AccountFactory(title="From")
    a_to = AccountFactory(title="To")

    IncomeFactory(account=a_from, date=date(1998, 1, 1), price=6)
    ExpenseFactory(account=a_from, date=date(1998, 1, 1), price=5)

    IncomeFactory(account=a_to, date=date(1998, 1, 1), price=5)
    ExpenseFactory(account=a_to, date=date(1998, 1, 1), price=3)

    if balances_emptied:
        AccountBalanceModelService(main_user).objects.delete()

    TransactionFactory(
        date=date(1999, 1, 1), from_account=a_from, to_account=a_to, price=1
    )

    assert account_rows(main_user) == [
        AccountRow("From", 1998, 0, 6, 5, 1, -1),
        AccountRow("From", 1999, 1, 0, 1, 0, 0),
        AccountRow("From", 2000, 0, 0, 0, 0, 0),
        AccountRow("To", 1998, 0, 5, 3, 2, -2),
        AccountRow("To", 1999, 2, 1, 0, 3, -3),
        AccountRow("To", 2000, 3, 0, 0, 3, -3),
    ]


@pytest.mark.parametrize(
    "factory, from_factory, to_factory, accounts, funds", MOVES_OF_ONE_CENT
)
def test_new_price_syncs_balances(
    main_user, factory, from_factory, to_factory, accounts, funds
):
    move = reloaded(
        factory(
            from_account=from_factory(title="From"),
            to_account=to_factory(title="To"),
            price=5,
        )
    )
    move.price = 1
    move.save()

    assert account_rows(main_user) == accounts
    assert fund_rows(main_user) == funds


@pytest.mark.parametrize(
    "factory, from_factory, to_factory, accounts, funds", MOVES_OF_ONE_CENT
)
def test_save_with_nothing_changed_keeps_balances(
    main_user, factory, from_factory, to_factory, accounts, funds
):
    move = factory(
        from_account=from_factory(title="From"),
        to_account=to_factory(title="To"),
        price=1,
    )

    reloaded(move).save()

    assert account_rows(main_user) == accounts
    assert fund_rows(main_user) == funds


@pytest.mark.parametrize(
    "factory, from_factory, to_factory, accounts, funds", MOVES_OF_ONE_CENT
)
def test_new_ends_take_the_balances_from_the_old(
    main_user, factory, from_factory, to_factory, accounts, funds
):
    move = reloaded(
        factory(
            from_account=from_factory(title="Old-From"),
            to_account=to_factory(title="Old-To"),
            price=1,
        )
    )
    move.from_account = from_factory(title="From")
    move.to_account = to_factory(title="To")
    move.save()

    assert account_rows(main_user) == accounts
    assert fund_rows(main_user) == funds


@pytest.mark.parametrize("factory, from_factory, to_factory", MOVES)
def test_delete_drops_its_balances(main_user, factory, from_factory, to_factory):
    move = factory(
        from_account=from_factory(title="From"), to_account=to_factory(title="To")
    )

    reloaded(move).delete()

    assert account_rows(main_user) == []
    assert fund_rows(main_user) == []
    assert not type(move).objects.exists()


@pytest.mark.parametrize(
    "factory, from_factory, to_factory, accounts, funds", MOVES_OF_ONE_CENT
)
def test_delete_leaves_the_other_moves_balances(
    main_user, factory, from_factory, to_factory, accounts, funds
):
    ends = {
        "from_account": from_factory(title="From"),
        "to_account": to_factory(title="To"),
    }
    kept = factory(price=1, **ends)

    reloaded(factory(price=5, **ends)).delete()

    assert account_rows(main_user) == accounts
    assert fund_rows(main_user) == funds
    assert list(type(kept).objects.all()) == [kept]


def test_transaction_incomes_sum_each_receiver_by_year(main_user):
    sender = AccountFactory(title="From")
    a1 = AccountFactory(title="To1")
    a2 = AccountFactory(title="To2")
    ends = {"from_account": sender}
    TransactionFactory(date=date(1999, 1, 1), price=25, to_account=a1, **ends)
    TransactionFactory(date=date(1999, 6, 1), price=4, to_account=a1, **ends)
    TransactionFactory(date=date(1999, 1, 1), price=1, to_account=a2, **ends)
    TransactionFactory(date=date(1970, 1, 1), price=25, to_account=a1, **ends)

    actual = TransactionModelService(main_user).incomes()

    assert list(actual) == [
        {"year": 1970, "incomes": 25, "category_id": a1.pk},
        {"year": 1999, "incomes": 29, "category_id": a1.pk},
        {"year": 1999, "incomes": 1, "category_id": a2.pk},
    ]


@pytest.mark.parametrize(
    "service, factory, sender, receiver, with_fee, sums",
    [
        pytest.param(
            TransactionModelService,
            TransactionFactory,
            AccountFactory,
            AccountFactory,
            {},
            [(1970, {"expenses": 25}), (1999, {"expenses": 26})],
            id="transaction",
        ),
        pytest.param(
            SavingCloseModelService,
            SavingCloseFactory,
            SavingTypeFactory,
            AccountFactory,
            {"fee": 1},
            [(1970, {"expenses": 25, "fee": 1}), (1999, {"expenses": 26, "fee": 2})],
            id="saving_close",
        ),
        pytest.param(
            SavingChangeModelService,
            SavingChangeFactory,
            SavingTypeFactory,
            SavingTypeFactory,
            {"fee": 1},
            [(1970, {"expenses": 25, "fee": 1}), (1999, {"expenses": 26, "fee": 2})],
            id="saving_change",
        ),
    ],
)
def test_expenses_sum_each_sender_by_year(
    main_user, service, factory, sender, receiver, with_fee, sums
):
    fund = sender(title="Saving1")
    a1 = receiver(title="To1")
    a2 = receiver(title="To2")
    ends = {"from_account": fund, **with_fee}
    factory(date=date(1999, 1, 1), price=25, to_account=a1, **ends)
    factory(date=date(1999, 1, 1), price=1, to_account=a2, **ends)
    factory(date=date(1970, 1, 1), price=25, to_account=a1, **ends)

    actual = service(main_user).expenses()

    assert list(actual) == [
        {"year": year, **sum_, "category_id": fund.pk} for year, sum_ in sums
    ]


@pytest.mark.parametrize("factory, sender, receiver", MOVES)
def test_str_names_the_day_both_ends_and_the_grouped_price(factory, sender, receiver):
    move = factory.build(
        date=date(2001, 2, 3),
        price=123456,
        from_account=sender.build(title="Ex. Fund"),
        to_account=receiver.build(title="Ex. Bank"),
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


def test_saving_close_post_save_first_record(main_user):
    _to = AccountFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingFactory(saving_type=_from, price=40, date=date(1998, 1, 1), fee=2)
    IncomeFactory(account=_to, price=10, date=date(1998, 1, 1))

    SavingBalance.objects.all().delete()
    AccountBalance.objects.all().delete()

    SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    assert [row for row in account_rows(main_user) if row[0] == "To"] == [
        AccountRow("To", 1998, 0, 10, 0, 10, -10),
        AccountRow("To", 1999, 10, 1, 0, 11, -11),
        AccountRow("To", 2000, 11, 0, 0, 11, -11),
    ]
    assert fund_rows(main_user) == [
        FundRow("From", 1998, 0, 0, 2, 40),
        FundRow("From", 1999, 40, 2, 2, 40),
        FundRow("From", 2000, 40, 2, 2, 40),
    ]


@pytest.mark.parametrize("balances_emptied", [False, True], ids=["kept", "emptied"])
def test_saving_change_save_carries_each_funds_past(main_user, balances_emptied):
    _to = SavingTypeFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingFactory(saving_type=_to, price=50, date=date(1998, 1, 1), fee=2)
    SavingFactory(saving_type=_from, price=40, date=date(1998, 1, 1), fee=2)

    if balances_emptied:
        SavingBalance.objects.all().delete()

    SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    assert fund_rows(main_user) == [
        FundRow("From", 1998, 0, 0, 2, 40),
        FundRow("From", 1999, 40, 2, 2, 40),
        FundRow("From", 2000, 40, 2, 2, 40),
        FundRow("To", 1998, 0, 0, 2, 50),
        FundRow("To", 1999, 50, 2, 2, 51),
        FundRow("To", 2000, 51, 2, 2, 51),
    ]


@pytest.mark.parametrize(
    "factory, fund_factory",
    [
        pytest.param(TransactionFactory, AccountFactory, id="transaction"),
        pytest.param(SavingCloseFactory, SavingTypeFactory, id="saving_close"),
        pytest.param(SavingChangeFactory, SavingTypeFactory, id="saving_change"),
    ],
)
def test_move_journal_is_its_from_accounts(second_user, factory, fund_factory):
    journal = second_user.journal

    obj = factory.build(from_account=fund_factory(journal=journal))

    assert obj.journal == journal
