from datetime import date

import pytest
import time_machine

from ....accounts.tests.factories import AccountFactory
from ....bookkeeping import balance_sources
from ....savings.models import SavingType
from ....savings.tests.factories import SavingTypeFactory
from ....transactions.close_rules import KEEP
from ....transactions.forms import SavingChangeForm, SavingCloseForm
from ....transactions.tests.factories import SavingChangeFactory, SavingCloseFactory

pytestmark = pytest.mark.django_db

FACTORIES = {"sell": SavingCloseFactory, "switch": SavingChangeFactory}
FORMS = {"sell": SavingCloseForm, "switch": SavingChangeForm}


@pytest.mark.parametrize("move", FACTORIES)
def test_move_saved_without_a_form_keeps_the_close_year(move):
    fund = SavingTypeFactory(title="Fund", closed=1999)

    FACTORIES[move](from_account=fund, date="2000-06-01")

    fund.refresh_from_db()
    assert fund.closed == 1999


@pytest.mark.parametrize("move", FACTORIES)
def test_move_saved_without_a_form_leaves_an_open_fund_open(move):
    fund = SavingTypeFactory(title="Fund")

    FACTORIES[move](from_account=fund, date="2000-06-01")

    fund.refresh_from_db()
    assert fund.closed is None


def _ticked_form(main_user, move, close=True):
    fund = SavingTypeFactory(title="Fund")
    receiver = (
        SavingTypeFactory(title="Other") if move == "switch" else AccountFactory()
    )
    form = FORMS[move](
        user=main_user,
        today=date(1999, 1, 1),
        data={
            "date": "1999-01-01",
            "from_account": fund.pk,
            "to_account": receiver.pk,
            "price": "5",
            "fee": "0.5",
            "close": close,
        },
    )
    assert form.is_valid()
    return fund, form


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize(
    "close, closed",
    [pytest.param(True, 1999, id="closes"), pytest.param(False, None, id="kept")],
)
@pytest.mark.parametrize("move, accounts", [("sell", 1), ("switch", 0)])
def test_form_move_syncs_once_whether_it_closes_the_fund_or_not(
    main_user, mocker, move, accounts, close, closed
):
    fund, form = _ticked_form(main_user, move, close)
    savings = mocker.spy(balance_sources, "sync_savings")
    balances = mocker.spy(balance_sources, "sync_accounts")

    form.save()

    fund.refresh_from_db()
    assert fund.closed == closed
    assert savings.call_count == 1
    assert balances.call_count == accounts


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", FACTORIES)
def test_deleting_the_closing_move_syncs_once_and_reopens_the_fund(
    main_user, mocker, move
):
    fund, form = _ticked_form(main_user, move)
    row = form.save()
    savings = mocker.spy(balance_sources, "sync_savings")

    row.delete()

    fund.refresh_from_db()
    assert fund.closed is None
    assert savings.call_count == 1


@pytest.mark.parametrize("move", FACTORIES)
def test_move_saved_without_a_form_to_another_fund_follows_the_one_it_left(move):
    first = SavingTypeFactory(title="First", closed=1999)
    second = SavingTypeFactory(title="Second")
    FACTORIES[move](from_account=first, date="2000-06-01")
    row = FACTORIES[move]._meta.model.objects.get()

    row.from_account = second
    row.save()

    first.refresh_from_db()
    assert first.closed == 1999


@pytest.mark.parametrize(
    "second_day, closed, deleted",
    [
        # a close year set on the fund form, later than any move
        pytest.param(date(1999, 6, 1), 2001, 0, id="earlier"),
        pytest.param(date(1999, 6, 1), 2001, 1, id="last"),
        # a move left on the closing day is the closing move now
        pytest.param(date(1999, 3, 1), 1999, 1, id="same_day_as_another"),
    ],
)
@pytest.mark.parametrize("move", FACTORIES)
def test_deleting_a_move_that_is_not_the_closing_one_keeps_the_close_year(
    move, second_day, closed, deleted
):
    fund = SavingTypeFactory(title="Fund")
    rows = [
        FACTORIES[move](from_account=fund, date=day)
        for day in (date(1999, 3, 1), second_day)
    ]
    SavingType.objects.filter(pk=fund.pk).update(closed=closed)

    rows[deleted].delete()

    fund.refresh_from_db()
    assert fund.closed == closed


@pytest.mark.parametrize("move", FACTORIES)
def test_move_saved_again_without_a_form_leaves_a_fund_it_left_alone(move):
    first = SavingTypeFactory(title="First", closed=1999)
    second = SavingTypeFactory(title="Second")
    FACTORIES[move](from_account=first, date="2000-06-01")
    row = FACTORIES[move]._meta.model.objects.get()
    row.from_account = second
    row.save()
    SavingType.objects.filter(pk=first.pk).update(closed=2005)

    row.save()

    first.refresh_from_db()
    assert first.closed == 2005


@time_machine.travel("1999-1-1")
@pytest.mark.parametrize("move", FACTORIES)
def test_form_unticked_box_is_not_applied_to_a_later_save_of_the_row(main_user, move):
    fund = SavingTypeFactory(title="Fund")
    receiver = (
        SavingTypeFactory(title="Other") if move == "switch" else AccountFactory()
    )
    form = FORMS[move](
        user=main_user,
        today=date(1999, 1, 1),
        data={
            "date": "1999-01-01",
            "from_account": fund.pk,
            "to_account": receiver.pk,
            "price": "5",
            "close": False,
        },
    )
    assert form.is_valid()
    row = form.save()
    SavingType.objects.filter(pk=fund.pk).update(closed=1999)

    row.save()

    fund.refresh_from_db()
    assert fund.closed == 1999
    assert row.close_rule is KEEP
