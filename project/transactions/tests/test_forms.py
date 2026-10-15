from datetime import date
from typing import Callable, NamedTuple

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...bookkeeping import balance_sources
from ...savings.models import SavingBalance, SavingType
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm

pytestmark = pytest.mark.django_db

TODAY = date(1999, 1, 1)


class _Kind(NamedTuple):
    form: type
    source: Callable
    target: Callable
    fields: tuple


_FIELDS = (
    '<input type="text" name="date"',
    '<select name="to_account"',
    '<select name="from_account"',
    '<input type="text" name="price"',
)
_FEE_FIELDS = ('<input type="text" name="fee"', '<input type="checkbox" name="close"')

KINDS = {
    "transaction": _Kind(TransactionForm, AccountFactory, AccountFactory, _FIELDS),
    "saving_change": _Kind(
        SavingChangeForm, SavingTypeFactory, SavingTypeFactory, _FIELDS + _FEE_FIELDS
    ),
    "saving_close": _Kind(
        SavingCloseForm, SavingTypeFactory, AccountFactory, _FIELDS + _FEE_FIELDS
    ),
}
FEE_KINDS = ["saving_change", "saving_close"]


def _parents(kind, **kwargs):
    return kind.source(title="From", **kwargs), kind.target(title="To", **kwargs)


def _post(a_from, a_to, **fields):
    return {
        "date": "1999-01-01",
        "from_account": a_from.pk,
        "to_account": a_to.pk,
    } | fields


@pytest.mark.parametrize("name", KINDS)
def test_form_fields(main_user, name):
    form = KINDS[name].form(user=main_user, today=TODAY).as_p()

    for field in KINDS[name].fields:
        assert field in form


@pytest.mark.parametrize("name", KINDS)
def test_form_year_initial_value(main_user, name):
    form = KINDS[name].form(user=main_user, today=date(1974, 1, 1)).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


@pytest.mark.parametrize("name", ["transaction", "saving_change"])
def test_form_selected_parent(main_user, second_user, name):
    kind = KINDS[name]
    a_from = kind.source(title="From")
    kind.source(title="Theirs", journal=second_user.journal)

    form = kind.form(
        user=main_user, today=TODAY, data={"from_account": a_from.pk}
    ).as_p()

    assert f'<option value="{a_from.pk}" selected>From</option>' in form
    assert f'<option value="{a_from.pk}">From</option>' not in form


@pytest.mark.parametrize("name", ["transaction", "saving_change"])
def test_form_non_numeric_from_account_is_invalid(main_user, name):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)

    form = kind.form(
        user=main_user,
        today=TODAY,
        data=_post(a_from, a_to, price="1", from_account="x"),
    )

    assert not form.is_valid()
    assert "from_account" in form.errors


@pytest.mark.parametrize("name", ["transaction", "saving_change"])
def test_form_edit_offers_every_parent_but_the_stored_from_account(main_user, name):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)
    saved = kind.form(user=main_user, today=TODAY, data=_post(a_from, a_to, price="1"))
    assert saved.is_valid()
    row = saved.save()

    form = kind.form(user=main_user, today=TODAY, instance=row)

    assert ">To</option>" in str(form["to_account"])
    assert ">From</option>" not in str(form["to_account"])


@pytest.mark.parametrize("name", FEE_KINDS)
def test_form_close_label_marks_the_from_account(main_user, name):
    form = KINDS[name].form(user=main_user, today=TODAY)

    assert "Uždaryti <b>Iš sąskaitos</b>" in form["close"].label_tag()


@pytest.mark.parametrize("posted, cents", [("0.01", 1), ("12,1", 1210)])
@pytest.mark.parametrize("name", KINDS)
def test_form_valid_data(main_user, name, posted, cents):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)

    form = kind.form(
        user=main_user, today=TODAY, data=_post(a_from, a_to, price=posted)
    )

    assert form.is_valid(), form.errors

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == cents
    assert data.from_account == a_from
    assert data.to_account == a_to


@pytest.mark.parametrize(
    "fields, cents",
    [
        pytest.param({"fee": "0.01"}, 1, id="fee"),
        pytest.param({"fee": "0,55"}, 55, id="decimal_comma"),
        pytest.param({}, 0, id="no_fee"),
    ],
)
@pytest.mark.parametrize("name", FEE_KINDS)
def test_form_fee_is_stored_in_cents(main_user, name, fields, cents):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)

    form = kind.form(
        user=main_user, today=TODAY, data=_post(a_from, a_to, price="0.01", **fields)
    )

    assert form.is_valid(), form.errors
    assert form.save().fee == cents


@pytest.mark.parametrize("year", [1998, 2001])
@pytest.mark.parametrize("name", KINDS)
def test_form_invalid_date(main_user, name, year):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)

    form = kind.form(
        user=main_user,
        today=TODAY,
        data=_post(a_from, a_to, date=f"{year}-01-01", price="1.0"),
    )

    assert not form.is_valid()
    assert "date" in form.errors
    assert "Metai turi būti tarp 1999 ir 2000" in form.errors["date"]


@pytest.mark.parametrize("name", KINDS)
def test_form_blank_data(main_user, name):
    form = KINDS[name].form(user=main_user, today=TODAY, data={})

    assert not form.is_valid()

    assert "date" in form.errors
    assert "from_account" in form.errors
    assert "to_account" in form.errors
    assert "price" in form.errors


@pytest.mark.parametrize("name", KINDS)
def test_form_price_null(main_user, name):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)

    form = kind.form(user=main_user, today=TODAY, data=_post(a_from, a_to, price="0"))

    assert not form.is_valid()

    assert "price" in form.errors


@pytest.mark.parametrize(
    "year, closed_listed",
    [
        pytest.param(3000, False, id="closed_in_past"),
        pytest.param(1000, True, id="closed_in_future"),
        pytest.param(2000, True, id="closed_in_current_year"),
    ],
)
@pytest.mark.parametrize("name", FEE_KINDS)
def test_form_lists_a_fund_closed_only_up_to_the_year(
    main_user, name, year, closed_listed
):
    main_user.year = year

    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    form = KINDS[name].form(user=main_user, today=TODAY, data={})

    assert "S1" in str(form["from_account"])
    assert ("S2" in str(form["from_account"])) is closed_listed

    assert "S1" not in str(form["to_account"])
    assert "S2" not in str(form["to_account"])


@pytest.mark.parametrize("name", FEE_KINDS)
def test_form_save_and_close_from_account(main_user, name):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)

    form = kind.form(
        user=main_user,
        today=TODAY,
        data=_post(a_from, a_to, price="0.01", fee="0.01", close=True),
    )
    assert form.is_valid()

    form.save()

    assert SavingType.objects.get(title=a_from.title).closed == 1999


# sells and switches save the fund too
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
        lambda: AccountFactory(title="Bank"),
        lambda bank: AccountBalance.objects.get(account=bank, year=1999),
    ),
    "switch": _Move(
        SavingChangeForm,
        lambda: SavingTypeFactory(title="Other"),
        lambda other: SavingBalance.objects.get(saving_type=other, year=1999),
    ),
}


@pytest.fixture(name="fund")
def fixture_fund():
    return SavingTypeFactory(title="Fund")


@pytest.fixture(name="receiver")
def fixture_receiver(move):
    return MOVES[move].receiver()


@pytest.mark.parametrize(
    "close, closed",
    [pytest.param(False, None, id="kept_open"), pytest.param(True, 1999, id="closed")],
)
@pytest.mark.parametrize(
    "fee_source, debit",
    [
        pytest.param(SavingType.FeeSource.INVESTMENT, 1000, id="investment"),
        pytest.param(SavingType.FeeSource.ACCOUNT, 1010, id="account"),
    ],
)
@pytest.mark.parametrize("move", MOVES)
def test_sell_and_switch_forms_leave_balances_a_re_sync_agrees_with(
    main_user, move, fee_source, debit, close, closed
):
    bank, fund = _purchase(fee_source)
    receiver = MOVES[move].receiver()
    data = {
        "date": "1999-01-01",
        "from_account": fund.pk,
        "to_account": receiver.pk,
        "price": "5",
        "fee": "0.5",
        "close": close,
    }

    form = MOVES[move].form(user=main_user, today=TODAY, data=data)
    assert form.is_valid()
    form.save()
    after_form = _balances()

    balance_sources.sync_accounts(user=main_user)
    balance_sources.sync_savings(user=main_user)

    assert AccountBalance.objects.get(account=bank, year=1999).expenses == debit
    assert MOVES[move].received(receiver).incomes == 500
    assert SavingType.objects.get(pk=fund.pk).closed == closed
    assert _balances() == after_form


# the fund is written only when its year moves
def _fund_updates(queries):
    return [q for q in queries if q["sql"].startswith('UPDATE "savings_savingtype"')]


def _move_data(fund, receiver, day, close):
    return {
        "date": day,
        "from_account": fund.pk,
        "to_account": receiver.pk,
        "price": "5",
        "fee": "0.5",
        "close": close,
    }


def _saved_move(main_user, move, fund, receiver, day, close, instance=None):
    form = MOVES[move].form(
        user=main_user,
        today=TODAY,
        instance=instance,
        data=_move_data(fund, receiver, day, close),
    )
    assert form.is_valid()
    return form.save()


@pytest.mark.parametrize("move", MOVES)
def test_form_unticked_close_does_not_write_an_open_fund(
    main_user, move, fund, receiver
):
    with CaptureQueriesContext(connection) as queries:
        _saved_move(main_user, move, fund, receiver, "1999-01-01", False)

    assert _fund_updates(queries.captured_queries) == []


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_with_close_ticked_moves_the_close_year(
    main_user, move, fund, receiver
):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", True)
    assert SavingType.objects.get(pk=fund.pk).closed == 1999

    _saved_move(main_user, move, fund, receiver, "2000-01-01", True, row)

    assert SavingType.objects.get(pk=fund.pk).closed == 2000


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_of_an_earlier_sell_keeps_the_close_year(
    main_user, move, fund, receiver
):
    earlier = _saved_move(main_user, move, fund, receiver, "1999-01-01", False)
    _saved_move(main_user, move, fund, receiver, "2000-01-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-01-02", True, earlier)

    assert SavingType.objects.get(pk=fund.pk).closed == 2000


@pytest.mark.parametrize("move", MOVES)
def test_form_new_sell_before_the_close_year_keeps_it(main_user, move, fund, receiver):
    _saved_move(main_user, move, fund, receiver, "2000-01-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-01-01", True)

    assert SavingType.objects.get(pk=fund.pk).closed == 2000


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_with_close_unticked_reopens_the_fund(
    main_user, move, fund, receiver
):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-01-01", False, row)

    assert SavingType.objects.get(pk=fund.pk).closed is None


# a fund's close year follows its last move
@pytest.mark.parametrize("move", MOVES)
@pytest.mark.parametrize(
    "earlier_day, edited_day, edited_close",
    [
        pytest.param("2000-03-01", "1999-03-01", True, id="edited_back"),
        pytest.param("2000-09-01", "2000-06-01", False, id="unticked"),
        pytest.param(
            "1999-03-01", "1999-06-01", False, id="unticked_in_an_earlier_year"
        ),
    ],
)
def test_form_earlier_move_edited_keeps_the_fund_closed_in_its_last_year(
    main_user, move, fund, receiver, earlier_day, edited_day, edited_close
):
    earlier = _saved_move(main_user, move, fund, receiver, earlier_day, False)
    _saved_move(main_user, move, fund, receiver, "2000-12-01", True)

    _saved_move(main_user, move, fund, receiver, edited_day, edited_close, earlier)

    fund.refresh_from_db()
    assert fund.closed == 2000


@pytest.mark.parametrize("move", MOVES)
def test_form_new_unticked_move_before_the_last_keeps_the_fund_closed(
    main_user, move, fund, receiver
):
    _saved_move(main_user, move, fund, receiver, "1999-12-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-06-01", False)

    fund.refresh_from_db()
    assert fund.closed == 1999


@pytest.mark.parametrize("move", MOVES)
@pytest.mark.parametrize(
    "first_day, first_close, second_day",
    [
        pytest.param("1999-06-01", True, "1999-12-01", id="unticked_after_the_last"),
        pytest.param("2000-12-01", False, "2000-06-01", id="unticked_before_the_last"),
    ],
)
def test_form_new_unticked_move_leaves_the_fund_open(
    main_user, move, fund, receiver, first_day, first_close, second_day
):
    _saved_move(main_user, move, fund, receiver, first_day, first_close)

    _saved_move(main_user, move, fund, receiver, second_day, False)

    fund.refresh_from_db()
    assert fund.closed is None


@pytest.mark.parametrize("move", MOVES)
def test_form_closing_move_moved_to_another_fund_reopens_the_first(
    main_user, move, receiver
):
    first = SavingTypeFactory(title="First")
    second = SavingTypeFactory(title="Second")
    row = _saved_move(main_user, move, first, receiver, "1999-12-01", True)

    _saved_move(main_user, move, second, receiver, "1999-12-01", True, row)

    first.refresh_from_db()
    assert first.closed is None
    second.refresh_from_db()
    assert second.closed == 1999


@pytest.mark.parametrize("move", MOVES)
def test_form_move_moved_away_leaves_the_first_closed_at_its_last_move(
    main_user, move, receiver
):
    first = SavingTypeFactory(title="First")
    second = SavingTypeFactory(title="Second")
    _saved_move(main_user, move, first, receiver, "1999-06-01", False)
    row = _saved_move(main_user, move, first, receiver, "2000-12-01", True)

    _saved_move(main_user, move, second, receiver, "2000-12-01", False, row)

    first.refresh_from_db()
    assert first.closed == 1999
    second.refresh_from_db()
    assert second.closed is None


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_of_an_earlier_move_does_not_write_a_closed_fund(
    main_user, move, fund, receiver
):
    earlier = _saved_move(main_user, move, fund, receiver, "1999-03-01", False)
    _saved_move(main_user, move, fund, receiver, "1999-12-01", True)

    with CaptureQueriesContext(connection) as queries:
        _saved_move(main_user, move, fund, receiver, "1999-04-01", True, earlier)

    assert _fund_updates(queries.captured_queries) == []
    fund.refresh_from_db()
    assert fund.closed == 1999


@pytest.mark.parametrize("move", MOVES)
def test_form_closing_move_writes_the_fund_once(main_user, move, fund, receiver):
    with CaptureQueriesContext(connection) as queries:
        _saved_move(main_user, move, fund, receiver, "1999-12-01", True)

    assert len(_fund_updates(queries.captured_queries)) == 1


@pytest.mark.parametrize("move", MOVES)
def test_form_closing_move_edited_earlier_and_unticked_reopens_the_fund(
    main_user, move, fund, receiver
):
    _saved_move(main_user, move, fund, receiver, "2000-09-01", False)
    closing = _saved_move(main_user, move, fund, receiver, "2000-12-01", True)

    _saved_move(main_user, move, fund, receiver, "2000-06-01", False, closing)

    fund.refresh_from_db()
    assert fund.closed is None


# a stored fee of 0 is read as nothing entered
def _fee_less_move(main_user, move, fund, receiver):
    data = _move_data(fund, receiver, "1999-01-01", False) | {"fee": ""}
    form = MOVES[move].form(user=main_user, today=TODAY, data=data)
    assert form.is_valid()
    return form.save(), data


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_shows_a_stored_zero_fee_as_an_empty_field(
    main_user, move, fund, receiver
):
    row, _data = _fee_less_move(main_user, move, fund, receiver)

    form = MOVES[move].form(user=main_user, today=TODAY, instance=row)

    assert " value=" not in form["fee"].as_widget()


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_posts_its_own_empty_fee_back_and_saves_zero(
    main_user, move, fund, receiver
):
    row, data = _fee_less_move(main_user, move, fund, receiver)
    shown = MOVES[move].form(user=main_user, today=TODAY, instance=row)

    edit = MOVES[move].form(
        user=main_user,
        today=TODAY,
        instance=row,
        data=data | {"fee": shown["fee"].value()},
    )

    assert edit.is_valid(), edit.errors
    assert edit.save().fee == 0


@pytest.mark.parametrize("move", MOVES)
def test_form_edit_shows_a_stored_fee_as_it_is(main_user, move, fund, receiver):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", False)

    edit = MOVES[move].form(user=main_user, today=TODAY, instance=row)

    assert edit["fee"].value() == row.fee


# A posted id of another journal is rejected
@pytest.mark.parametrize("field", ["from_account", "to_account"])
@pytest.mark.parametrize("name", KINDS)
def test_form_rejects_a_parent_of_another_journal(main_user, second_user, name, field):
    kind = KINDS[name]
    a_from, a_to = _parents(kind, journal=main_user.journal)
    data = _post(a_from, a_to, price="0.01")
    foreign = {"from_account": kind.source, "to_account": kind.target}[field]
    data[field] = foreign(title="Theirs", journal=second_user.journal).pk

    form = kind.form(user=main_user, today=TODAY, data=data)

    assert not form.is_valid()
    assert field in form.errors
