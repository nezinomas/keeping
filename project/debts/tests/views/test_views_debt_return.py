import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ... import models
from ...services.model_services import DebtReturnModelService
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES, RETURN_TAB_PATHS

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


@pytest.mark.parametrize(
    "debt_type, other_factory, label",
    [
        pytest.param(
            models.Debt.DebtType.BORROW,
            factories.LendReturnFactory,
            "Paskolos davėjas",
            id="borrow",
        ),
        pytest.param(
            models.Debt.DebtType.LEND,
            factories.BorrowReturnFactory,
            "Paskolos gavėjas",
            id="lend",
        ),
    ],
)
def test_a_return_tab_with_data(client_logged, debt_type, other_factory, label):
    obj = RETURN_FACTORIES[debt_type](
        price=543_210, debt__name="Own name", debt__closed=True
    )
    other_factory(price=666_666, debt__name="Other name")

    content = client_logged.get(RETURN_TAB_PATHS[debt_type]).content.decode("utf-8")

    assert '<th class="text-left">Data</th>' in content
    assert f'<th class="text-left main__name">{label}</th>' in content
    assert '<th class="price-col">Suma</th>' in content
    assert '<th class="text-left main__fold">Sąskaita</th>' in content
    assert '<th class="text-left main__fold">Pastaba</th>' in content
    assert '<th class="price-col text-center">Uždaryta</th>' in content
    assert '<th class="edit-col"></th>' in content
    assert '<th class="delete-col"></th>' in content

    assert '<td class="text-left main__date">1999-01-02</td>' in content
    assert f'<td class="text-left main__name">{obj.debt.name}</td>' in content
    assert '<td class="main__figure" data-cell="">5.432,10</td>' in content
    assert '<td class="text-left main__fold">Account1</td>' in content
    assert (
        '<td class="text-center"><i class="bi bi-check-circle-fill"></i></td>'
        in content
    )

    assert '<td class="text-left main__name">Other name</td>' not in content
    assert '<td class="main__figure" data-cell="">6.666,66</td>' not in content


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
NAME_CELL = re.compile(r'<td class="text-left main__name">([^<]*)</td>')


@pytest.mark.parametrize(
    "debts, divided",
    [
        pytest.param(
            [("A", False, 2), ("B", False, 1)],
            [("", "A"), ("", "A"), ("table-group-divider", "B")],
            id="name",
        ),
        pytest.param(
            [("A", False, 1), ("A", True, 1)],
            [("", "A"), ("table-group-divider", "A")],
            id="closed",
        ),
    ],
)
def test_a_return_tab_divides_its_debts(client_logged, debts, divided):
    returns = []
    for name, closed, count in debts:
        debt = factories.BorrowFactory(name=name, closed=closed)
        returns += factories.BorrowReturnFactory.create_batch(count, debt=debt)

    content = client_logged.get("/debts/borrow/returns/").content.decode("utf-8")
    rows = RETURN_ROW.findall(content)

    assert [
        (divider, NAME_CELL.search(cells)[1]) for *_, divider, cells in rows
    ] == divided
    assert {(get, trigger, target) for get, trigger, target, *_ in rows} == {
        (
            reverse("debts:return_update", kwargs={"pk": r.pk, "debt_type": "borrow"}),
            "dblclick",
            "#mainModal",
        )
        for r in returns
    }
