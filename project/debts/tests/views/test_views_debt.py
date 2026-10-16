from datetime import date

import pytest
import time_machine
from django.test import Client
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ... import models
from ...services.model_services import DebtModelService
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "debt_type, other_factory",
    [
        pytest.param(models.Debt.DebtType.BORROW, factories.LendFactory, id="borrow"),
        pytest.param(models.Debt.DebtType.LEND, factories.BorrowFactory, id="lend"),
    ],
)
def test_debt_list_empty(client_logged, debt_type, other_factory):
    other_factory(price=666)

    url = reverse("debts:list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert "<b>1999</b> metais įrašų nėra" in content


@pytest.mark.parametrize(
    "debt_type, other_factory, label, remark",
    [
        pytest.param(
            models.Debt.DebtType.BORROW,
            factories.LendFactory,
            "Paskolos davėjas",
            "Borrow Remark",
            id="borrow",
        ),
        pytest.param(
            models.Debt.DebtType.LEND,
            factories.BorrowFactory,
            "Paskolos gavėjas",
            "Lend Remark",
            id="lend",
        ),
    ],
)
def test_debt_list_with_data(client_logged, debt_type, other_factory, label, remark):
    # both named: the assertions match substrings, and Faker cannot promise two
    # distinguishable names
    obj1 = DEBT_FACTORIES[debt_type](
        name="Own name", closed=True, price=777_777, returned=543_210
    )
    obj2 = other_factory(name="Other name", price=666_666)

    url = reverse("debts:list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert '">Data</th>' in content
    assert label in content
    assert '">Suma</th>' in content
    assert '">Gražinta</th>' in content
    assert '">Sąskaita</th>' in content
    assert '">Pastaba</th>' in content
    assert '">Uždaryta</th>' in content

    assert "1999-01-01" in content
    assert obj1.name in content
    assert "7.777,77" in content
    assert "5.432,10" in content
    assert '<td class="text-left cell-padding">Account1</td>' in content
    assert remark in content
    assert '<i class="bi bi-check-circle-fill"></i>' in content

    assert obj2.name not in content
    assert "6.666,66" not in content


@pytest.mark.parametrize("url_name", ["debts:update", "debts:delete"])
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_list_links_each_row_button(client_logged, debt_type, url_name):
    obj = DEBT_FACTORIES[debt_type]()

    url = reverse("debts:list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    link = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})

    assert f'<a role="button" hx-get="{link}"' in content


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@time_machine.travel("2000-01-01")
def test_debt_load_form(client_logged, debt_type):
    url = reverse("debts:new", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    actual = response.context["form"].as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in actual
    assert f'hx-post="{url}"' in response.content.decode()


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_save(main_user, client_logged, debt_type):
    a = AccountFactory()

    data = {"date": "1999-01-01", "name": "AAA", "price": "1", "account": a.pk}
    url = reverse("debts:new", kwargs={"debt_type": debt_type})
    client_logged.post(url, data)

    actual = DebtModelService(main_user, debt_type).items().get()
    assert actual.date == date(1999, 1, 1)
    assert actual.account.title == "Account1"
    assert actual.name == "AAA"
    assert actual.price == 1_00
    assert actual.debt_type == debt_type


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_save_invalid_data(client_logged, debt_type):
    data = {"date": "x", "name": "A", "price": "0"}
    url = reverse("debts:new", kwargs={"debt_type": debt_type})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert sorted(form.errors) == ["account", "date", "name", "price"]


@pytest.mark.parametrize(
    "debt_type, remark",
    [
        pytest.param(models.Debt.DebtType.BORROW, "Borrow Remark", id="borrow"),
        pytest.param(models.Debt.DebtType.LEND, "Lend Remark", id="lend"),
    ],
)
def test_debt_load_update_form(client_logged, debt_type, remark):
    f = DEBT_FACTORIES[debt_type](price=1)
    url = reverse("debts:update", kwargs={"pk": f.pk, "debt_type": debt_type})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert form.instance.account.title == "Account1"
    assert form.instance.remark == remark
    assert f'hx-post="{url}"' in response.content.decode()


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@pytest.mark.parametrize(
    "existing",
    [
        pytest.param({}, id="renamed"),
        pytest.param({"name": "XXX"}, id="name_kept"),
    ],
)
def test_debt_update(main_user, client_logged, debt_type, existing):
    e = DEBT_FACTORIES[debt_type](**existing)

    data = {
        "name": "XXX",
        "price": "0.01",
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": e.account.pk,
        "closed": False,
    }
    url = reverse("debts:update", kwargs={"pk": e.pk, "debt_type": debt_type})
    client_logged.post(url, data)

    actual = DebtModelService(main_user, debt_type).items().get()
    assert actual.name == "XXX"
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.account.title == "Account1"
    assert actual.remark == "Pastaba"
    assert not actual.closed


@pytest.mark.parametrize(
    "price, closed, returns, field, message",
    [
        pytest.param(
            "1",
            False,
            (4_00,),
            "price",
            "Skola negali būti mažesnė nei grąžinta suma.",
            id="price_smaller_then_returned",
        ),
        pytest.param(
            "150",
            True,
            (),
            "closed",
            "Negalite uždaryti dar negražintos skolos.",
            id="cant_close",
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_update_invalid(
    client_logged, debt_type, price, closed, returns, field, message
):
    debt = DEBT_FACTORIES[debt_type](name="XXX", price=5)
    for returned in returns:
        RETURN_FACTORIES[debt_type](debt=debt, price=returned)

    data = {
        "name": "XXX",
        "price": price,
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": debt.account.pk,
        "closed": closed,
    }
    url = reverse("debts:update", kwargs={"pk": debt.pk, "debt_type": debt_type})
    response = client_logged.post(url, data)

    assert response.context["form"].errors == {field: [message]}


@pytest.mark.parametrize(
    "url_name, send",
    [
        pytest.param("debts:update", Client.get, id="update_get"),
        pytest.param("debts:update", Client.post, id="update_post"),
        pytest.param("debts:delete", Client.get, id="delete_get"),
        pytest.param("debts:delete", Client.post, id="delete_post"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_of_other_journal_is_404(
    client_logged, second_user, debt_type, url_name, send
):
    a1 = AccountFactory(title="a1")
    a2 = AccountFactory(journal=second_user.journal, title="a2")

    DEBT_FACTORIES[debt_type](name="xxx", account=a1)
    obj = DEBT_FACTORIES[debt_type](
        name="yyy", price=666, journal=second_user.journal, account=a2
    )
    data = {"name": "zzz", "price": "1", "date": "1999-12-31", "account": a2.pk}

    url = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = send(client_logged, url, data)

    assert response.status_code == 404
    actual = models.Debt.objects.get(pk=obj.pk)
    assert (actual.name, actual.price) == ("yyy", 666)


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_delete_load_form(client_logged, debt_type):
    obj = DEBT_FACTORIES[debt_type]()

    url = reverse("debts:delete", kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_delete(client_logged, debt_type):
    p = DEBT_FACTORIES[debt_type]()

    url = reverse("debts:delete", kwargs={"pk": p.pk, "debt_type": debt_type})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert not models.Debt.objects.filter(pk=p.pk).exists()
