from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.forms.models import model_to_dict
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ...accounts.models import AccountBalance
from ...accounts.tests.factories import AccountFactory
from ...bookkeeping import balance_sources
from ...bookkeeping.tests.factories import SavingWorthFactory
from ...bookkeeping.tests.helper import quiet_build
from ...plans.tests.factories import SavingPlanFactory
from ...savings.forms import SavingTypeForm
from ...savings.models import SavingBalance, SavingType
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ..forms import SavingChangeForm
from .factories import SavingChangeFactory
from .kinds import FUND_MOVES, KINDS

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]

TODAY = date(1999, 1, 1)

_FIELDS = (
    '<input type="text" name="date"',
    '<select name="to_account"',
    '<select name="from_account"',
    '<input type="text" name="price"',
)
_FEE_FIELDS = ('<input type="text" name="fee"', '<input type="checkbox" name="close"')


def _parents(kind, **kwargs):
    return (
        kind.from_factory(title="From", **kwargs),
        kind.to_factory(title="To", **kwargs),
    )


def _post(a_from, a_to, **fields):
    return {
        "date": "1999-01-01",
        "from_account": a_from.pk,
        "to_account": a_to.pk,
    } | fields


@pytest.mark.parametrize("name", KINDS)
def test_form_fields(main_user, name):
    kind = KINDS[name]
    form = kind.form(user=main_user, today=TODAY).as_p()
    fields = _FIELDS
    if kind.fund_move:
        fields += _FEE_FIELDS

    for field in fields:
        assert field in form


@pytest.mark.parametrize("name", KINDS)
def test_form_date_widget(main_user, name):
    form = KINDS[name].form(user=main_user, today=TODAY)

    assert form["date"].widget_type == "datepicker"


LEFT_AFTER_FEE = "Suma kuri lieka atskaičius mokesčius"


@pytest.mark.parametrize(
    ("name", "field", "label", "help_text"),
    [
        (name, field, label, "")
        for name in KINDS
        for field, label in [
            ("date", "Data"),
            ("from_account", "Iš sąskaitos"),
            ("to_account", "Į sąskaitą"),
        ]
    ]
    + [("transaction", "price", "Suma", "")]
    + [
        (name, field, label, help_text)
        for name in FUND_MOVES
        for field, label, help_text in [
            ("price", "Suma", LEFT_AFTER_FEE),
            ("fee", "Mokesčiai", ""),
            ("close", "Uždaryti iš sąskaitos", ""),
        ]
    ],
)
def test_form_labels(main_user, name, field, label, help_text):
    form = KINDS[name].form(user=main_user, today=TODAY)

    assert (form[field].label, form[field].help_text) == (label, help_text)


@pytest.mark.parametrize(
    "name, url_name",
    [
        pytest.param("transaction", "accounts:load", id="transaction"),
        pytest.param("switch", "transactions:load_saving_type", id="switch"),
    ],
)
def test_form_from_account_loads_the_to_accounts(main_user, name, url_name):
    form = KINDS[name].form(user=main_user, today=TODAY)

    html = str(form["from_account"])

    assert f'hx-get="{reverse(url_name)}"' in html
    assert 'hx-target="#id_to_account"' in html
    assert 'hx-trigger="change"' in html


@pytest.mark.parametrize("name", KINDS)
def test_form_year_initial_value(main_user, name):
    form = KINDS[name].form(user=main_user, today=date(1974, 1, 1)).as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


@pytest.mark.parametrize("name", ["transaction", "switch"])
def test_form_selected_parent(main_user, second_user, name):
    kind = KINDS[name]
    a_from = kind.from_factory(title="From")
    kind.from_factory(title="Theirs", journal=second_user.journal)

    form = kind.form(
        user=main_user, today=TODAY, data={"from_account": a_from.pk}
    ).as_p()

    assert f'<option value="{a_from.pk}" selected>From</option>' in form
    assert f'<option value="{a_from.pk}">From</option>' not in form


@pytest.mark.parametrize("name", ["transaction", "switch"])
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


@pytest.mark.parametrize("name", ["transaction", "switch"])
def test_form_edit_offers_every_parent_but_the_stored_from_account(main_user, name):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)
    saved = kind.form(user=main_user, today=TODAY, data=_post(a_from, a_to, price="1"))
    assert saved.is_valid()
    row = saved.save()

    form = kind.form(user=main_user, today=TODAY, instance=row)

    assert ">To</option>" in str(form["to_account"])
    assert ">From</option>" not in str(form["to_account"])


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
@pytest.mark.parametrize("name", FUND_MOVES)
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


FUND_ERROR = "Fondas uždarytas 1999."
ACCOUNT_ERROR = (
    "Data negali būti vėlesnė nei sąskaitos uždarymo data. Sąskaita buvo uždaryta 1999."
)


@pytest.mark.parametrize(
    "name, fields, posted, errors",
    [
        pytest.param(
            "switch",
            ["to_account"],
            "2000-03-01",
            {"to_account": [FUND_ERROR]},
            id="switch_into",
        ),
        pytest.param(
            "switch",
            ["from_account"],
            "2000-03-01",
            {"date": [FUND_ERROR]},
            id="switch_out_of",
        ),
        pytest.param(
            "sale",
            ["from_account"],
            "2000-03-01",
            {"date": [FUND_ERROR]},
            id="sell_out_of",
        ),
        pytest.param(
            "sale",
            ["to_account"],
            "2000-03-01",
            {"date": [ACCOUNT_ERROR]},
            id="sell_into",
        ),
        pytest.param(
            "transaction",
            ["from_account"],
            "2000-03-01",
            {"date": [ACCOUNT_ERROR]},
            id="transfer_from",
        ),
        pytest.param(
            "transaction",
            ["to_account"],
            "2000-03-01",
            {"date": [ACCOUNT_ERROR]},
            id="transfer_to",
        ),
        pytest.param(
            "transaction",
            ["from_account", "to_account"],
            "2000-03-01",
            {"date": [ACCOUNT_ERROR, ACCOUNT_ERROR]},
            id="transfer_both",
        ),
        pytest.param(
            "sale", ["to_account"], "1999-12-31", {}, id="sell_into_closed_year"
        ),
        pytest.param(
            "transaction",
            ["from_account", "to_account"],
            "1999-12-31",
            {},
            id="transfer_closed_year",
        ),
    ],
)
def test_form_date_after_the_parent_closed(main_user, name, fields, posted, errors):
    kind = KINDS[name]
    a_from, a_to = _parents(kind)
    for field in fields:
        closed = {"from_account": a_from, "to_account": a_to}[field]
        closed.closed = 1999
        closed.save()

    form = kind.form(
        user=main_user,
        today=TODAY,
        data=_post(a_from, a_to, date=posted, price="1.0"),
    )

    assert form.errors == errors


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
@pytest.mark.parametrize("name", FUND_MOVES)
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


@pytest.fixture(name="fund")
def fixture_fund():
    return SavingTypeFactory(title="Fund")


@pytest.fixture(name="receiver")
def fixture_receiver(move):
    return KINDS[move].to_factory(title="To")


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
@pytest.mark.parametrize("move", FUND_MOVES)
@pytest.mark.syncs
def test_sell_and_switch_forms_leave_balances_a_re_sync_agrees_with(
    main_user, move, fee_source, debit, close, closed
):
    with quiet_build(main_user):
        bank, fund = _purchase(fee_source)
        receiver = KINDS[move].to_factory(title="To")
    data = _move_data(fund, receiver, "1999-01-01", close)

    form = KINDS[move].form(user=main_user, today=TODAY, data=data)
    assert form.is_valid()
    form.save()
    after_form = _balances()

    balance_sources.sync_accounts(user=main_user)
    balance_sources.sync_savings(user=main_user)

    assert AccountBalance.objects.get(account=bank, year=1999).expenses == debit
    assert KINDS[move].received(receiver).incomes == 500
    assert SavingType.objects.get(pk=fund.pk).closed == closed
    assert _balances() == after_form


def _fund_updates(queries):
    return [q for q in queries if q["sql"].startswith('UPDATE "savings_savingtype"')]


def _move_data(fund, receiver, day, close):
    return _post(fund, receiver, date=day, price="5", fee="0.5", close=close)


def _saved_move(main_user, move, fund, receiver, day, close, instance=None):
    form = KINDS[move].form(
        user=main_user,
        today=TODAY,
        instance=instance,
        data=_move_data(fund, receiver, day, close),
    )
    assert form.is_valid()
    return form.save()


@pytest.mark.parametrize("move", FUND_MOVES)
def test_form_closing_move_edited_past_the_close_year_is_rejected(
    main_user, move, fund, receiver
):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", True)
    assert SavingType.objects.get(pk=fund.pk).closed == 1999

    form = KINDS[move].form(
        user=main_user,
        today=TODAY,
        instance=row,
        data=_move_data(fund, receiver, "2000-01-01", True),
    )

    assert form.errors == {"date": ["Fondas uždarytas 1999."]}
    assert SavingType.objects.get(pk=fund.pk).closed == 1999


FUND_ROWS_IN_2000 = {
    "buy": lambda fund: SavingFactory(saving_type=fund, date=date(2000, 1, 1)),
    "switch_in": lambda fund: SavingChangeFactory(
        to_account=fund, date=date(2000, 1, 1)
    ),
    "worth": lambda fund: SavingWorthFactory(
        saving_type=fund,
        date=datetime(2000, 6, 1, 12, tzinfo=ZoneInfo("Europe/Vilnius")),
    ),
    "plan": lambda fund: SavingPlanFactory(saving_type=fund, year=2000),
}
CANT_CLOSE_BEFORE_2000 = {
    "close": ["Negalima uždaryti anksčiau nei 2000: tais metais yra įrašų."]
}


# each returns the move the ticked form edits; None for a new one, as Django takes it
def _a_new_move(main_user, move, fund, receiver):
    return None


def _a_later_move_edited(main_user, move, fund, receiver):
    return _saved_move(main_user, move, fund, receiver, "2000-12-01", False)


def _a_later_move_kept(main_user, move, fund, receiver):
    _saved_move(main_user, move, fund, receiver, "2000-12-01", False)


@pytest.mark.parametrize(
    "setup, row, move, day, close, errors",
    [
        pytest.param(
            _a_new_move,
            "buy",
            "sale",
            "1999-06-01",
            True,
            CANT_CLOSE_BEFORE_2000,
            id="before-buy-sale",
        ),
        pytest.param(
            _a_new_move,
            "switch_in",
            "switch",
            "1999-06-01",
            True,
            CANT_CLOSE_BEFORE_2000,
            id="before-switch_in-switch",
        ),
        pytest.param(
            _a_new_move,
            "worth",
            "sale",
            "1999-06-01",
            True,
            CANT_CLOSE_BEFORE_2000,
            id="before-worth-sale",
        ),
        pytest.param(
            _a_new_move,
            "plan",
            "sale",
            "1999-06-01",
            True,
            CANT_CLOSE_BEFORE_2000,
            id="before-plan-sale",
        ),
        pytest.param(
            _a_later_move_edited,
            "buy",
            "sale",
            "1999-06-01",
            True,
            CANT_CLOSE_BEFORE_2000,
            id="edited_back-buy-sale",
        ),
        pytest.param(
            _a_later_move_edited,
            "buy",
            "switch",
            "1999-06-01",
            True,
            CANT_CLOSE_BEFORE_2000,
            id="edited_back-buy-switch",
        ),
        pytest.param(
            _a_later_move_kept,
            "buy",
            "sale",
            "1999-06-01",
            True,
            {},
            id="a_later_move_closes-buy-sale",
        ),
        pytest.param(
            _a_later_move_kept,
            "buy",
            "switch",
            "1999-06-01",
            True,
            {},
            id="a_later_move_closes-buy-switch",
        ),
        pytest.param(
            _a_new_move,
            "buy",
            "sale",
            "2000-06-01",
            True,
            {},
            id="in_the_row_year-buy-sale",
        ),
        pytest.param(
            _a_new_move,
            "buy",
            "sale",
            "1999-06-01",
            False,
            {},
            id="unticked-buy-sale",
        ),
    ],
)
def test_form_tick_closing_before_a_fund_row(
    main_user, move, fund, receiver, row, setup, day, close, errors
):
    edited = setup(main_user, move, fund, receiver)
    FUND_ROWS_IN_2000[row](fund)

    form = KINDS[move].form(
        user=main_user,
        today=TODAY,
        instance=edited,
        data=_move_data(fund, receiver, day, close),
    )

    assert form.errors == errors


def test_form_switch_reversed_onto_its_old_target_can_close_it(main_user, fund):
    source = SavingTypeFactory(title="Source")
    target = SavingTypeFactory(title="Target")
    switch = _saved_move(main_user, "switch", source, fund, "2000-12-01", False)

    form = SavingChangeForm(
        user=main_user,
        today=TODAY,
        instance=switch,
        data=_move_data(fund, target, "1999-06-01", True),
    )

    assert form.errors == {}


@pytest.mark.parametrize("move", FUND_MOVES)
def test_form_edit_with_close_unticked_reopens_the_fund(
    main_user, move, fund, receiver
):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", True)

    _saved_move(main_user, move, fund, receiver, "1999-01-01", False, row)

    assert SavingType.objects.get(pk=fund.pk).closed is None


@pytest.mark.parametrize("move", FUND_MOVES)
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


@pytest.mark.parametrize("move", FUND_MOVES)
@pytest.mark.parametrize(
    "saved, posted, edits, closed",
    [
        pytest.param(
            [("1999-12-01", True)],
            ("1999-06-01", False),
            None,
            1999,
            id="unticked_before_the_closing_move",
        ),
        pytest.param(
            [("2000-12-01", False)],
            ("2000-06-01", False),
            None,
            None,
            id="unticked_on_an_open_fund",
        ),
        pytest.param(
            [("1999-03-01", False), ("1999-12-01", True)],
            ("1999-04-01", True),
            0,
            1999,
            id="earlier_move_ticked",
        ),
    ],
)
def test_form_move_that_leaves_the_close_year_writes_no_fund(
    main_user, move, fund, receiver, saved, posted, edits, closed
):
    moves = [_saved_move(main_user, move, fund, receiver, *row) for row in saved]
    # None: a new move, as Django's form takes it
    instance = None if edits is None else moves[edits]

    with CaptureQueriesContext(connection) as queries:
        _saved_move(main_user, move, fund, receiver, *posted, instance)

    assert _fund_updates(queries.captured_queries) == []
    fund.refresh_from_db()
    assert fund.closed == closed


@pytest.mark.parametrize("move", FUND_MOVES)
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


@pytest.mark.parametrize("move", FUND_MOVES)
@pytest.mark.parametrize(
    "second_closed",
    [
        pytest.param(None, id="onto_an_open_fund"),
        pytest.param(2001, id="onto_a_closed"),
    ],
)
def test_form_closing_move_moved_away_unticked_reopens_the_first(
    main_user, move, receiver, second_closed
):
    first = SavingTypeFactory(title="First")
    second = SavingTypeFactory(title="Second", closed=second_closed)
    _saved_move(main_user, move, first, receiver, "1999-06-01", False)
    row = _saved_move(main_user, move, first, receiver, "2000-12-01", True)

    _saved_move(main_user, move, second, receiver, "2000-12-01", False, row)

    first.refresh_from_db()
    assert first.closed is None
    second.refresh_from_db()
    assert second.closed == second_closed


@pytest.mark.parametrize("move", FUND_MOVES)
@pytest.mark.parametrize(
    "box",
    [
        pytest.param(lambda form: form["close"].initial, id="as_rendered"),
        pytest.param(lambda form: False, id="unticked"),
    ],
)
def test_form_edit_of_a_move_keeps_a_close_year_set_on_the_fund_form(
    main_user, move, fund, receiver, box
):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", False)
    fund_form = SavingTypeForm(
        user=main_user,
        today=TODAY,
        instance=fund,
        data=model_to_dict(fund) | {"closed": 2001},
    )
    assert fund_form.is_valid()
    fund_form.save()

    close = box(KINDS[move].form(user=main_user, today=TODAY, instance=row))
    form = KINDS[move].form(
        user=main_user,
        today=TODAY,
        instance=row,
        data=_move_data(fund, receiver, "1999-01-01", close) | {"price": "6"},
    )
    assert form.is_valid()
    form.save()

    fund.refresh_from_db()
    assert fund.closed == 2001


@pytest.mark.parametrize("move", FUND_MOVES)
def test_form_closing_move_writes_the_fund_once(main_user, move, fund, receiver):
    with CaptureQueriesContext(connection) as queries:
        _saved_move(main_user, move, fund, receiver, "1999-12-01", True)

    assert len(_fund_updates(queries.captured_queries)) == 1


def _fee_less_move(main_user, move, fund, receiver):
    data = _move_data(fund, receiver, "1999-01-01", False) | {"fee": ""}
    form = KINDS[move].form(user=main_user, today=TODAY, data=data)
    assert form.is_valid()
    return form.save(), data


@pytest.mark.parametrize("move", FUND_MOVES)
def test_form_edit_shows_a_stored_zero_fee_as_an_empty_field(
    main_user, move, fund, receiver
):
    row, _data = _fee_less_move(main_user, move, fund, receiver)

    form = KINDS[move].form(user=main_user, today=TODAY, instance=row)

    assert " value=" not in form["fee"].as_widget()


@pytest.mark.parametrize("move", FUND_MOVES)
def test_form_edit_posts_its_own_empty_fee_back_and_saves_zero(
    main_user, move, fund, receiver
):
    row, data = _fee_less_move(main_user, move, fund, receiver)
    shown = KINDS[move].form(user=main_user, today=TODAY, instance=row)

    edit = KINDS[move].form(
        user=main_user,
        today=TODAY,
        instance=row,
        data=data | {"fee": shown["fee"].value()},
    )

    assert edit.is_valid(), edit.errors
    assert edit.save().fee == 0


@pytest.mark.parametrize("move", FUND_MOVES)
def test_form_edit_shows_a_stored_fee_as_it_is(main_user, move, fund, receiver):
    row = _saved_move(main_user, move, fund, receiver, "1999-01-01", False)

    edit = KINDS[move].form(user=main_user, today=TODAY, instance=row)

    assert edit["fee"].value() == row.fee


@pytest.mark.parametrize("field", ["from_account", "to_account"])
@pytest.mark.parametrize("name", KINDS)
def test_form_rejects_a_parent_of_another_journal(main_user, second_user, name, field):
    kind = KINDS[name]
    a_from, a_to = _parents(kind, journal=main_user.journal)
    data = _post(a_from, a_to, price="0.01")
    foreign = {"from_account": kind.from_factory, "to_account": kind.to_factory}[field]
    data[field] = foreign(title="Theirs", journal=second_user.journal).pk

    form = kind.form(user=main_user, today=TODAY, data=data)

    assert not form.is_valid()
    assert field in form.errors
