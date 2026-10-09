from datetime import date

import pytest
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
    "debt_type, other_factory, price, other_price, remark",
    [
        pytest.param(
            "borrow",
            factories.LendReturnFactory,
            "0,05",
            "0,06",
            "Borrow Return Remark",
            id="borrow",
        ),
        pytest.param(
            "lend",
            factories.BorrowReturnFactory,
            "0,06",
            "0,05",
            "Lend Return Remark",
            id="lend",
        ),
    ],
)
def test_debt_return_list_with_data(
    client_logged, debt_type, other_factory, price, other_price, remark
):
    RETURN_FACTORIES[debt_type]()
    other_factory(price=6.6)

    url = reverse("debts:return_list", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert "Data" in content
    assert "Suma" in content
    assert "Sąskaita" in content
    assert "Pastaba" in content

    assert "1999-01-02" in content
    assert price in content
    assert "Account1" in content
    assert remark in content

    assert other_price not in content


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
def test_debt_return_load_form(client_logged, debt_type):
    url = reverse("debts:return_new", kwargs={"debt_type": debt_type})
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert f'hx-post="{url}"' in content


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_save(main_user, client_logged, debt_type):
    a = AccountFactory()
    b = DEBT_FACTORIES[debt_type]()

    data = {"date": "1999-1-3", "debt": b.pk, "price": "1", "account": a.pk}
    url = reverse("debts:return_new", kwargs={"debt_type": debt_type})
    client_logged.post(url, data, follow=True)

    actual = DebtReturnModelService(main_user, debt_type).items()[0]
    assert actual.date == date(1999, 1, 3)
    assert actual.account.title == "Account1"
    assert actual.price == 100


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_save_invalid_data(client_logged, debt_type):
    data = {debt_type: "A", "price": "0"}
    url = reverse("debts:return_new", kwargs={"debt_type": debt_type})
    response = client_logged.post(url, data)
    form = response.context["form"]

    assert not form.is_valid()


@pytest.mark.parametrize(
    "debt_type, remark",
    [
        pytest.param("borrow", "Borrow Return Remark", id="borrow"),
        pytest.param("lend", "Lend Return Remark", id="lend"),
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


@pytest.mark.parametrize(
    "debt_type, returned",
    [pytest.param("borrow", 5, id="borrow"), pytest.param("lend", 6, id="lend")],
)
def test_debt_return_update(client_logged, debt_type, returned):
    debt = DEBT_FACTORIES[debt_type](price=200)
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
    client_logged.post(url, data, follow=True)

    actual = models.DebtReturn.objects.get(pk=e.pk)
    assert actual.debt == debt
    assert actual.date == date(1999, 1, 2)
    assert actual.price == 100
    assert actual.account.title == "AAA"
    assert actual.remark == "Pastaba"
    assert models.Debt.objects.get(pk=debt.pk).returned == 100


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_update_with_returns(client_logged, debt_type):
    debt = DEBT_FACTORIES[debt_type](price=100 * 100)
    RETURN_FACTORIES[debt_type](debt=debt, price=40 * 100)
    RETURN_FACTORIES[debt_type](debt=debt, price=50 * 100)
    e = RETURN_FACTORIES[debt_type](debt=debt, price=5 * 100)
    a = AccountFactory(title="AAA")

    data = {
        "date": "1999-1-2",
        "price": "6",
        "remark": "Pastaba",
        "account": a.pk,
        "debt": debt.pk,
    }
    url = reverse("debts:return_update", kwargs={"pk": e.pk, "debt_type": debt_type})
    client_logged.post(url, data, follow=True)

    assert models.DebtReturn.objects.get(pk=e.pk).price == 600


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_update_not_load_other_journal(
    client_logged, second_user, debt_type
):
    a1 = AccountFactory(title="a1")
    a2 = AccountFactory(journal=second_user.journal, title="a2")
    d1 = DEBT_FACTORIES[debt_type](account=a1)
    d2 = DEBT_FACTORIES[debt_type](account=a2, journal=second_user.journal)

    RETURN_FACTORIES[debt_type](debt=d1, account=a1)
    obj = RETURN_FACTORIES[debt_type](debt=d2, account=a2, price=666)

    url = reverse("debts:return_update", kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_delete_load_form(client_logged, debt_type):
    obj = RETURN_FACTORIES[debt_type]()

    url = reverse("debts:return_delete", kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert response.status_code == 200
    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in actual


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_delete(client_logged, debt_type):
    p = RETURN_FACTORIES[debt_type]()

    assert models.DebtReturn.objects.all().count() == 1

    url = reverse("debts:return_delete", kwargs={"pk": p.pk, "debt_type": debt_type})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert models.DebtReturn.objects.all().count() == 0


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_delete_other_journal_get_form(
    client_logged, second_user, debt_type
):
    account = AccountFactory(journal=second_user.journal, title="a2")
    d = DEBT_FACTORIES[debt_type](journal=second_user.journal, account=account)
    obj = RETURN_FACTORIES[debt_type](debt=d, account=account)

    url = reverse("debts:return_delete", kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_return_delete_other_journal_post_form(
    client_logged, second_user, debt_type
):
    account = AccountFactory(journal=second_user.journal, title="a2")
    d = DEBT_FACTORIES[debt_type](journal=second_user.journal, account=account)
    obj = RETURN_FACTORIES[debt_type](debt=d, account=account)

    url = reverse("debts:return_delete", kwargs={"pk": obj.pk, "debt_type": debt_type})
    client_logged.post(url, follow=True)

    assert models.DebtReturn.objects.all().count() == 1
