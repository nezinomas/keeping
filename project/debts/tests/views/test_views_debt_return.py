from datetime import date

import pytest
import time_machine
from django.test import Client
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ... import models
from ...services.model_services import DebtReturnModelService
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_list_empty(client_logged, debt_type):
    url = reverse("debts:return_list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert "<b>1999</b> metais įrašų nėra" in content


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

    assert "1999-01-02" in content
    assert '<td class="text-right cell-padding">5.432,10</td>' in content
    assert '<td class="text-left cell-padding">Account1</td>' in content
    assert remark in content

    assert "6.666,66" not in content


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
@time_machine.travel("2000-01-01")
def test_debt_return_load_form(client_logged, debt_type):
    url = reverse("debts:return_new", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    actual = response.context["form"].as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in actual
    assert f'hx-post="{url}"' in response.content.decode()


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


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_save_invalid_data(client_logged, debt_type):
    data = {"debt": "A", "price": "0"}
    url = reverse("debts:return_new", kwargs={"debt_type": debt_type})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert sorted(form.errors) == ["account", "date", "debt", "price"]


@pytest.mark.parametrize(
    "debt_type, remark",
    [
        pytest.param(models.Debt.DebtType.BORROW, "Borrow Return Remark", id="borrow"),
        pytest.param(models.Debt.DebtType.LEND, "Lend Return Remark", id="lend"),
    ],
)
def test_debt_return_load_update_form(client_logged, debt_type, remark):
    obj = RETURN_FACTORIES[debt_type](price=1)
    url = reverse("debts:return_update", kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 2)
    assert form.instance.price == 0.01
    assert form.instance.account.title == "Account1"
    assert form.instance.remark == remark
    assert f'hx-post="{url}"' in response.content.decode()


@pytest.mark.parametrize(
    "debt_type, returned",
    [
        pytest.param(models.Debt.DebtType.BORROW, 5, id="borrow"),
        pytest.param(models.Debt.DebtType.LEND, 6, id="lend"),
    ],
)
def test_debt_return_update(client_logged, debt_type, returned):
    debt = DEBT_FACTORIES[debt_type](price=2_00)
    e = RETURN_FACTORIES[debt_type](debt=debt)
    a = AccountFactory(title="AAA")

    assert models.Debt.objects.get(pk=debt.pk).returned == returned

    data = {
        "date": "1999-1-2",
        "price": "1",
        "remark": "Pastaba",
        "account": a.pk,
        "debt": debt.pk,
    }
    url = reverse("debts:return_update", kwargs={"pk": e.pk, "debt_type": debt_type})
    client_logged.post(url, data)

    actual = models.DebtReturn.objects.get(pk=e.pk)
    assert actual.debt == debt
    assert actual.date == date(1999, 1, 2)
    assert actual.price == 1_00
    assert actual.account.title == "AAA"
    assert actual.remark == "Pastaba"
    assert models.Debt.objects.get(pk=debt.pk).returned == 1_00


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_update_with_returns(client_logged, debt_type):
    debt = DEBT_FACTORIES[debt_type](price=100_00)
    RETURN_FACTORIES[debt_type](debt=debt, price=40_00)
    RETURN_FACTORIES[debt_type](debt=debt, price=50_00)
    e = RETURN_FACTORIES[debt_type](debt=debt, price=5_00)
    a = AccountFactory(title="AAA")

    data = {
        "date": "1999-1-2",
        "price": "6",
        "remark": "Pastaba",
        "account": a.pk,
        "debt": debt.pk,
    }
    url = reverse("debts:return_update", kwargs={"pk": e.pk, "debt_type": debt_type})
    client_logged.post(url, data)

    assert models.DebtReturn.objects.get(pk=e.pk).price == 6_00
    assert models.Debt.objects.get(pk=debt.pk).returned == 96_00


@pytest.mark.parametrize(
    "url_name, send",
    [
        pytest.param("debts:return_update", Client.get, id="update_get"),
        pytest.param("debts:return_update", Client.post, id="update_post"),
        pytest.param("debts:return_delete", Client.get, id="delete_get"),
        pytest.param("debts:return_delete", Client.post, id="delete_post"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_of_other_journal_is_404(
    client_logged, second_user, debt_type, url_name, send
):
    a1 = AccountFactory(title="a1")
    a2 = AccountFactory(journal=second_user.journal, title="a2")
    d1 = DEBT_FACTORIES[debt_type](account=a1)
    d2 = DEBT_FACTORIES[debt_type](account=a2, journal=second_user.journal)

    RETURN_FACTORIES[debt_type](debt=d1, account=a1)
    obj = RETURN_FACTORIES[debt_type](debt=d2, account=a2, price=666)
    data = {"date": "1999-1-2", "price": "1", "account": a2.pk, "debt": d2.pk}

    url = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = send(client_logged, url, data)

    assert response.status_code == 404
    assert models.DebtReturn.objects.get(pk=obj.pk).price == 666


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_delete_load_form(client_logged, debt_type):
    obj = RETURN_FACTORIES[debt_type]()

    url = reverse("debts:return_delete", kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_delete(client_logged, debt_type):
    p = RETURN_FACTORIES[debt_type]()

    url = reverse("debts:return_delete", kwargs={"pk": p.pk, "debt_type": debt_type})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert not models.DebtReturn.objects.filter(pk=p.pk).exists()
