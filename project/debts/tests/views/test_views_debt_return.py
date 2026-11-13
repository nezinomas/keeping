import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import ROW_BUTTON
from ... import models
from ...services.model_services import DebtReturnModelService
from ..helpers import (
    BORROW,
    DEBT_FACTORIES,
    DEBT_TYPES,
    NAME_CELL,
    RETURN_FACTORIES,
    RETURN_TAB_PATHS,
)

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_save(main_user, client_logged, debt_type):
    a = AccountFactory()
    b = DEBT_FACTORIES[debt_type]()

    data = {"date": "1999-1-3", "debt": b.pk, "price": "1", "account": a.pk}
    url = reverse("debts:return_new", kwargs={"debt_type": debt_type})
    client_logged.post(url, data)

    actual = DebtReturnModelService(main_user, debt_type).items().get()
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == "Account1"
    assert actual.price == 1_00
    assert actual.debt == b


@pytest.mark.parametrize(
    "others, before, price, saved, returned",
    [
        pytest.param((), 5_00, "1", 1_00, 1_00, id="alone"),
        pytest.param((40_00, 50_00), 95_00, "6", 6_00, 96_00, id="with_returns"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_update(
    client_logged, debt_type, others, before, price, saved, returned
):
    debt = DEBT_FACTORIES[debt_type](price=100_00)
    for other in others:
        RETURN_FACTORIES[debt_type](debt=debt, price=other)
    e = RETURN_FACTORIES[debt_type](debt=debt, price=5_00)
    a = AccountFactory(title="AAA")

    assert models.Debt.objects.get(pk=debt.pk).returned == before

    data = {
        "date": "1999-1-2",
        "price": price,
        "remark": "Pastaba",
        "account": a.pk,
        "debt": debt.pk,
    }
    url = reverse("debts:return_update", kwargs={"pk": e.pk, "debt_type": debt_type})
    client_logged.post(url, data)

    actual = models.DebtReturn.objects.get(pk=e.pk)
    assert actual.debt == debt
    assert actual.date == date(1999, 1, 2)
    assert actual.price == saved
    assert actual.account.title == "AAA"
    assert actual.remark == "Pastaba"
    assert models.Debt.objects.get(pk=debt.pk).returned == returned


RETURN_ROW = re.compile(
    r'<tr(?: hx-get="([^"]+)" hx-trigger="([^"]*)" hx-target="([^"]*)")? '
    r'class="([^"]*)">(.*?)</tr>',
    re.DOTALL,
)


@pytest.mark.parametrize(
    "debts, divided",
    [
        pytest.param(
            [("A", False, [2, 2]), ("B", False, [2])],
            [("", "A"), ("", "A"), ("table-group-divider", "B")],
            id="name",
        ),
        pytest.param(
            [("A", False, [2]), ("A", True, [2])],
            [("", "A"), ("table-group-divider", "A")],
            id="closed",
        ),
        # one name, one date: the Returns' days interleave unless the Debt orders them
        pytest.param(
            [("A", True, [4, 2]), ("A", True, [3])],
            [("", "A"), ("", "A"), ("table-group-divider", "A")],
            id="two_closed_of_one_name",
        ),
    ],
)
def test_a_return_tab_divides_its_debts(client_logged, debts, divided):
    for name, closed, days in debts:
        debt = DEBT_FACTORIES[BORROW](name=name, closed=closed)
        for day in days:
            RETURN_FACTORIES[BORROW](debt=debt, date=date(1999, 1, day))

    content = client_logged.get(RETURN_TAB_PATHS[BORROW]).content.decode("utf-8")
    rows = RETURN_ROW.findall(content)

    assert [
        (divider, NAME_CELL.search(cells)[1]) for *_, divider, cells in rows
    ] == divided


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_closed_debts_return_row_opens_nothing(client_logged, debt_type):
    # the open row first: a Closed row must not keep the url the row above drew
    open_return = RETURN_FACTORIES[debt_type](debt__name="Open")
    closed = DEBT_FACTORIES[debt_type](name="Shut", closed=True)
    RETURN_FACTORIES[debt_type](debt=closed)

    content = client_logged.get(RETURN_TAB_PATHS[debt_type]).content.decode("utf-8")
    rows = [
        (get, ROW_BUTTON.findall(cells))
        for get, _trigger, _target, _divider, cells in RETURN_ROW.findall(content)
    ]

    kwargs = {"pk": open_return.pk, "debt_type": debt_type}
    update = reverse("debts:return_update", kwargs=kwargs)
    assert rows == [
        (
            update,
            [
                ("edit-col", update),
                ("delete-col", reverse("debts:return_delete", kwargs=kwargs)),
            ],
        ),
        ("", []),
    ]
