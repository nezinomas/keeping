import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ... import models
from ...services.model_services import DebtReturnModelService
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_list_empty(client_logged, debt_type):
    url = reverse("debts:return_list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert re.search(
        r'<div class="alert alert-warning">\s*1999 metais įrašų nėra\.\s*</div>',
        content,
    )


@pytest.mark.parametrize(
    "debt_type, other_factory, remark",
    [
        pytest.param(
            models.Debt.DebtType.BORROW,
            factories.LendReturnFactory,
            "Borrow Return Remark",
            id="borrow",
        ),
        pytest.param(
            models.Debt.DebtType.LEND,
            factories.BorrowReturnFactory,
            "Lend Return Remark",
            id="lend",
        ),
    ],
)
def test_debt_return_list_with_data(client_logged, debt_type, other_factory, remark):
    RETURN_FACTORIES[debt_type](price=543_210)
    other_factory(price=666_666)

    url = reverse("debts:return_list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '">Data</th>' in content
    assert '">Suma</th>' in content
    assert '">Sąskaita</th>' in content
    assert '">Pastaba</th>' in content

    assert '<td class="text-center">1999-01-02</td>' in content
    assert '<td class="text-right cell-padding">5.432,10</td>' in content
    assert '<td class="text-left cell-padding">Account1</td>' in content
    assert f'<td class="text-left">{remark}</td>' in content

    assert '<td class="text-right cell-padding">6.666,66</td>' not in content


@pytest.mark.parametrize("url_name", ["debts:return_update", "debts:return_delete"])
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_list_links_each_row_button(client_logged, debt_type, url_name):
    obj = RETURN_FACTORIES[debt_type]()

    url = reverse("debts:return_list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    link = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})

    assert f'<a role="button" hx-get="{link}"' in content


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
    r'<tr hx-get="([^"]*)" hx-trigger="([^"]*)" hx-target="([^"]*)" class="([^"]*)">'
    r'\s*<td[^>]*>[^<]*</td>\s*<td class="text-left cell-padding">([^<]*)</td>'
)


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
def test_debt_return_list_divides_its_debts(client_logged, debts, divided):
    returns = []
    for name, closed, count in debts:
        debt = factories.BorrowFactory(name=name, closed=closed)
        returns += factories.BorrowReturnFactory.create_batch(count, debt=debt)

    url = reverse("debts:return_list", kwargs={"debt_type": "borrow"})
    rows = RETURN_ROW.findall(client_logged.get(url).content.decode("utf-8"))

    assert [(divider, name) for *_, divider, name in rows] == divided
    assert {(get, trigger, target) for get, trigger, target, *_ in rows} == {
        (
            reverse("debts:return_update", kwargs={"pk": r.pk, "debt_type": "borrow"}),
            "dblclick",
            "#mainModal",
        )
        for r in returns
    }
