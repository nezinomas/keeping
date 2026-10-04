from datetime import date
from typing import Callable, NamedTuple

import pytest
import time_machine
from django.db.models.signals import post_save

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...core.services import signals_service
from ...savings.models import SavingBalance, SavingType
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ...users.tests.factories import UserFactory
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_init(main_user):
    TransactionForm(user=main_user)


def test_transaction_init_fields(main_user):
    form = TransactionForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="text" name="price"' in form
    assert '<select name="from_account"' in form
    assert '<select name="to_account"' in form


@time_machine.travel("1974-01-01")
def test_transaction_year_initial_value(main_user):
    UserFactory()

    form = TransactionForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_transaction_current_user_accounts(main_user, second_user):
    AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = TransactionForm(user=main_user).as_p()

    assert "A1" in form
    assert "A2" not in form


def test_transaction_current_user_accounts_selected_parent(main_user, second_user):
    a1 = AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = TransactionForm(user=main_user, data={"from_account": a1.pk}).as_p()

    assert '<option value="1" selected>A1</option>' in form
    assert '<option value="1">A1</option>' not in form


def test_transaction_valid_data(main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.from_account == a_from
    assert data.to_account == a_to


@time_machine.travel("1999-1-1")
def test_transaction_price_accepts_a_decimal_comma(main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "12,1",
        },
    )

    assert form.is_valid(), form.errors
    assert form.save().price == 1210


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_transaction_invalid_date(year, main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "1.0",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_transaction_blank_data(main_user):
    form = TransactionForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


def test_transaction_price_null(main_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title="Account2")

    form = TransactionForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0",
        },
    )

    assert not form.is_valid()

    assert "price" in form.errors


# ----------------------------------------------------------------------------
#                                                                Saving Change
# ----------------------------------------------------------------------------
def test_saving_change_init(main_user):
    SavingChangeForm(user=main_user)


def test_saving_change_fields(main_user):
    form = SavingChangeForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="to_account"' in form
    assert '<select name="from_account"' in form
    assert '<input type="text" name="price"' in form
    assert '<input type="text" name="fee"' in form
    assert '<input type="checkbox" name="close"' in form


@time_machine.travel("1974-01-01")
def test_saving_change_year_initial_value(main_user):
    UserFactory()

    form = SavingChangeForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_change_current_user(main_user, second_user):
    SavingTypeFactory(title="S1")  # user bob, current user
    SavingTypeFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingChangeForm(user=main_user).as_p()

    assert "S1" in form
    assert "S2" not in form


def test_saving_change_current_user_accounts_selected_parent(main_user, second_user):
    s1 = SavingTypeFactory(title="S1")  # user bob, current user
    SavingTypeFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingChangeForm(user=main_user, data={"from_account": s1.pk}).as_p()

    assert '<option value="1" selected>S1</option>' in form
    assert '<option value="1">S1</option>' not in form


def test_saving_change_valid_data(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_saving_change_price_and_fee_accept_a_decimal_comma(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "12,1",
            "fee": "0,55",
        },
    )

    assert form.is_valid(), form.errors

    data = form.save()

    assert data.price == 1210
    assert data.fee == 55


def test_saving_change_valid_data_with_no_fee(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.from_account == a_from
    assert data.to_account == a_to


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_saving_change_invalid_date(year, main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "1.0",
            "fee": "0.25",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_saving_change_blank_data(main_user):
    form = SavingChangeForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


def test_saving_change_price_null(main_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title="Savings2")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0",
        },
    )

    assert not form.is_valid()

    assert "price" in form.errors


def test_saving_change_form_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingChangeForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" not in str(form["from_account"])

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


def test_saving_change_form_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingChangeForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


def test_saving_change_form_type_closed_in_current_year(main_user):
    main_user.year = 2000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingChangeForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


@time_machine.travel("1999-1-1")
def test_saving_change_save_and_close_from_account(main_user):
    a_from = SavingTypeFactory(title="From")
    a_to = SavingTypeFactory(title="To")

    form = SavingChangeForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
            "close": True,
        },
    )
    assert form.is_valid()

    form.save()

    actual = SavingType.objects.get(title=a_from.title)

    assert actual.closed == 1999


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_init(main_user):
    SavingCloseForm(user=main_user)


def test_saving_close_fields(main_user):
    form = SavingCloseForm(user=main_user).as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="to_account"' in form
    assert '<select name="from_account"' in form
    assert '<input type="text" name="price"' in form
    assert '<input type="text" name="fee"' in form
    assert '<input type="checkbox" name="close"' in form


@time_machine.travel("1974-01-01")
def test_saving_close_year_initial_value(main_user):
    UserFactory()

    form = SavingCloseForm(user=main_user).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_close_current_user_saving_types(main_user, second_user):
    SavingTypeFactory(title="S1")  # user bob, current user
    SavingTypeFactory(title="S2", journal=second_user.journal)  # user X

    form = SavingCloseForm(user=main_user).as_p()

    assert "S1" in form
    assert "S2" not in form


def test_saving_close_current_user_accounts(main_user, second_user):
    AccountFactory(title="A1")  # user bob, current user
    AccountFactory(title="A2", journal=second_user.journal)  # user X

    form = SavingCloseForm(user=main_user).as_p()

    assert "A1" in form
    assert "A2" not in form


def test_saving_close_valid_data(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_saving_close_price_and_fee_accept_a_decimal_comma(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "12,1",
            "fee": "0,55",
        },
    )

    assert form.is_valid(), form.errors

    data = form.save()

    assert data.price == 1210
    assert data.fee == 55


def test_saving_close_valid_data_no_fee(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
        },
    )

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.from_account == a_from
    assert data.to_account == a_to


@time_machine.travel("1999-2-2")
@pytest.mark.parametrize("year", [1998, 2001])
def test_saving_close_in_valid_date(year, main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": f"{year}-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "1.0",
            "fee": "0.25",
        },
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


def test_saving_close_blank_data(main_user):
    form = SavingCloseForm(user=main_user, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


def test_saving_close_price_null(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0",
        },
    )

    assert not form.is_valid()

    assert "price" in form.errors


def test_saving_close_form_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingCloseForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" not in str(form["from_account"])


def test_saving_close_form_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingCloseForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])


def test_saving_close_form_type_closed_in_current_year(main_user):
    main_user.year = 2000

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = SavingCloseForm(user=main_user, data={})

    assert "S1" in str(form["from_account"])
    assert "S2" in str(form["from_account"])


@time_machine.travel("1999-1-1")
def test_saving_close_save_and_close_saving_account(main_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title="Account2")

    form = SavingCloseForm(
        user=main_user,
        data={
            "date": "1999-01-01",
            "from_account": a_from.pk,
            "to_account": a_to.pk,
            "price": "0.01",
            "fee": "0.01",
            "close": True,
        },
    )

    assert form.is_valid()

    form.save()

    actual = SavingType.objects.get(title=a_from.title)

    assert actual.closed == 1999


# ----------------------------------------------------------------------------
#                                        sells and switches save the fund too
# ----------------------------------------------------------------------------
def _balances():
    return (
        sorted(
            AccountBalance.objects.values_list(
                "account__title", "year", "expenses", "incomes", "balance"
            )
        ),
        sorted(
            SavingBalance.objects.values_list(
                "saving_type__title", "year", "incomes", "fee", "sold", "sold_fee"
            )
        ),
    )


def _purchase(fee_source):
    bank = AccountFactory(title="Bank")
    fund = SavingTypeFactory(title="Fund", fee_source=fee_source)
    SavingFactory(account=bank, saving_type=fund, price=1000, fee=10)
    return bank, fund


class _Move(NamedTuple):
    form: type
    receiver: Callable
    received: Callable


MOVES = {
    "sell": _Move(
        SavingCloseForm,
        lambda bank, other: bank,
        lambda bank: AccountBalance.objects.get(account=bank, year=1999),
    ),
    "switch": _Move(
        SavingChangeForm,
        lambda bank, other: other,
        lambda other: SavingBalance.objects.get(saving_type=other, year=1999),
    ),
}


@pytest.mark.parametrize("close", [False, True])
@pytest.mark.parametrize("fee_source", SavingType.FeeSource.values)
@pytest.mark.parametrize("move", MOVES)
def test_sell_and_switch_forms_leave_balances_a_re_sync_agrees_with(
    main_user, move, fee_source, close
):
    bank, fund = _purchase(fee_source)
    receiver = MOVES[move].receiver(bank, SavingTypeFactory(title="Other"))
    data = {
        "date": "1999-01-01",
        "from_account": fund.pk,
        "to_account": receiver.pk,
        "price": "5",
        "fee": "0.5",
        "close": close,
    }

    form = MOVES[move].form(user=main_user, data=data)
    assert form.is_valid()
    form.save()
    after_form = _balances()

    signals_service.sync_accounts(instance=None, user=main_user)
    signals_service.sync_savings(instance=None, user=main_user)

    debit = 1010 if fee_source == SavingType.FeeSource.ACCOUNT else 1000
    assert AccountBalance.objects.get(account=bank, year=1999).expenses == debit
    assert MOVES[move].received(receiver).incomes == 500
    assert SavingType.objects.get(pk=fund.pk).closed == (1999 if close else None)
    assert _balances() == after_form


# ----------------------------------------------------------------------------
#                                      the fund is saved only when its year moves
# ----------------------------------------------------------------------------
class _TypeSaves:
    def __init__(self):
        self.count = 0

    def __call__(self, **kwargs):
        self.count += 1


@pytest.fixture
def type_saves():
    saves = _TypeSaves()
    post_save.connect(saves, sender=SavingType, weak=False)
    yield saves
    post_save.disconnect(saves, sender=SavingType)


def _move_data(fund, receiver, day, close):
    return {
        "date": day,
        "from_account": fund.pk,
        "to_account": receiver.pk,
        "price": "5",
        "fee": "0.5",
        "close": close,
    }


def _receiver(move, other):
    return other if move == "switch" else AccountFactory(title="Bank")


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_unticked_close_does_not_save_an_open_fund(main_user, move, type_saves):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    type_saves.count = 0

    form = MOVES[move].form(
        user=main_user, data=_move_data(fund, receiver, "1999-01-01", False)
    )
    assert form.is_valid()
    form.save()

    assert type_saves.count == 0


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_edit_with_close_ticked_moves_the_close_year(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    form = MOVES[move].form(
        user=main_user, data=_move_data(fund, receiver, "1999-01-01", True)
    )
    assert form.is_valid()
    row = form.save()
    assert SavingType.objects.get(pk=fund.pk).closed == 1999

    edit = MOVES[move].form(
        user=main_user,
        instance=row,
        data=_move_data(fund, receiver, "2000-01-01", True),
    )
    assert edit.is_valid()
    edit.save()

    assert SavingType.objects.get(pk=fund.pk).closed == 2000


def _saved_move(main_user, move, fund, receiver, day, close, instance=None):
    form = MOVES[move].form(
        user=main_user,
        instance=instance,
        data=_move_data(fund, receiver, day, close),
    )
    assert form.is_valid()
    return form.save()


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_edit_of_an_earlier_sell_keeps_the_close_year(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    earlier = _saved_move(main_user, move, fund, receiver, "1999-01-01", False)
    _saved_move(main_user, move, fund, receiver, "2000-01-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-01-02", True, earlier)

    assert SavingType.objects.get(pk=fund.pk).closed == 2000


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_new_sell_before_the_close_year_keeps_it(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    _saved_move(main_user, move, fund, receiver, "2000-01-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-01-01", True)

    assert SavingType.objects.get(pk=fund.pk).closed == 2000


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_edit_with_close_unticked_reopens_the_fund(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    form = MOVES[move].form(
        user=main_user, data=_move_data(fund, receiver, "1999-01-01", True)
    )
    assert form.is_valid()
    row = form.save()

    edit = MOVES[move].form(
        user=main_user,
        instance=row,
        data=_move_data(fund, receiver, "1999-01-01", False),
    )
    assert edit.is_valid()
    edit.save()

    assert SavingType.objects.get(pk=fund.pk).closed is None


# ----------------------------------------------------------------------------
#                                      a fund's close year follows its last move
# ----------------------------------------------------------------------------
def _closed(fund):
    return SavingType.objects.get(pk=fund.pk).closed


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_earlier_move_of_the_close_year_edited_back_keeps_the_close_year(
    main_user, move
):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    earlier = _saved_move(main_user, move, fund, receiver, "2000-03-01", False)
    _saved_move(main_user, move, fund, receiver, "2000-12-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-03-01", True, earlier)

    assert _closed(fund) == 2000


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_new_unticked_move_before_the_last_keeps_the_fund_closed(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    _saved_move(main_user, move, fund, receiver, "1999-12-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-06-01", False)

    assert _closed(fund) == 1999


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_new_unticked_move_after_the_last_reopens_the_fund(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    _saved_move(main_user, move, fund, receiver, "1999-06-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-12-01", False)

    assert _closed(fund) is None


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_closing_move_moved_to_another_fund_reopens_the_first(main_user, move):
    first = SavingTypeFactory(title="First")
    second = SavingTypeFactory(title="Second")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    row = _saved_move(main_user, move, first, receiver, "1999-12-01", True)

    _saved_move(main_user, move, second, receiver, "1999-12-01", True, row)

    assert _closed(first) is None
    assert _closed(second) == 1999


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_move_moved_away_leaves_the_first_closed_at_its_last_move(main_user, move):
    first = SavingTypeFactory(title="First")
    second = SavingTypeFactory(title="Second")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    _saved_move(main_user, move, first, receiver, "1999-06-01", False)
    row = _saved_move(main_user, move, first, receiver, "2000-12-01", True)

    _saved_move(main_user, move, second, receiver, "2000-12-01", False, row)

    assert _closed(first) == 1999
    assert _closed(second) is None


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_edit_of_an_earlier_move_does_not_save_a_closed_fund(
    main_user, move, type_saves
):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    earlier = _saved_move(main_user, move, fund, receiver, "1999-03-01", False)
    _saved_move(main_user, move, fund, receiver, "1999-12-01", True)
    type_saves.count = 0

    _saved_move(main_user, move, fund, receiver, "1999-04-01", True, earlier)

    assert type_saves.count == 0
    assert _closed(fund) == 1999


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_closing_move_edited_earlier_and_unticked_reopens_the_fund(
    main_user, move
):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    _saved_move(main_user, move, fund, receiver, "2000-09-01", False)
    closing = _saved_move(main_user, move, fund, receiver, "2000-12-01", True)

    _saved_move(main_user, move, fund, receiver, "2000-06-01", False, closing)

    assert _closed(fund) is None


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_earlier_move_edited_and_unticked_keeps_the_fund_closed(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    earlier = _saved_move(main_user, move, fund, receiver, "2000-09-01", False)
    _saved_move(main_user, move, fund, receiver, "2000-12-01", True)

    _saved_move(main_user, move, fund, receiver, "2000-06-01", False, earlier)

    assert _closed(fund) == 2000


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", MOVES)
def test_form_unticked_earlier_move_leaves_an_open_fund_open(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = _receiver(move, SavingTypeFactory(title="Other"))
    _saved_move(main_user, move, fund, receiver, "2000-12-01", False)

    _saved_move(main_user, move, fund, receiver, "2000-06-01", False)

    assert _closed(fund) is None
