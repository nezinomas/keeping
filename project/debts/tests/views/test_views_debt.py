import json
import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ... import models
from ...services.model_services import DebtModelService
from .. import factories
from ..helpers import (
    DEBT_FACTORIES,
    DEBT_TYPES,
    FIGURE_CELL,
    FOLDED_FIGURE,
    RETURN_FACTORIES,
    RETURN_TAB_PATHS,
    TAB_PATHS,
)

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


@pytest.mark.parametrize(
    "debt_type, other_factory, label",
    [
        pytest.param(
            models.Debt.DebtType.BORROW,
            factories.LendFactory,
            "Paskolos davėjas",
            id="borrow",
        ),
        pytest.param(
            models.Debt.DebtType.LEND,
            factories.BorrowFactory,
            "Paskolos gavėjas",
            id="lend",
        ),
    ],
)
def test_debt_tab_with_data(client_logged, debt_type, other_factory, label):
    # both named: Faker cannot promise two different names
    obj1 = DEBT_FACTORIES[debt_type](
        name="Own name", closed=True, price=777_777, returned=543_210
    )
    obj2 = other_factory(name="Other name", price=666_666)

    response = client_logged.get(TAB_PATHS[debt_type])
    content = response.content.decode("utf-8")

    assert '">Data</th>' in content
    assert f'<th class="text-left main__name">{label}</th>' in content
    assert '">Suma</th>' in content
    assert '">Grąžinta</th>' in content
    assert '">Sąskaita</th>' in content
    assert '">Pastaba</th>' in content
    assert '">Uždaryta</th>' not in content
    assert '<th class="edit-col"></th>' in content
    assert '<th class="delete-col"></th>' in content

    assert '<td class="text-left main__date">1999-01-01</td>' in content
    assert (
        f'<td class="text-left main__name">{obj1.name} '
        '<span class="main__closed">Grąžinta</span></td>'
    ) in content
    assert '<td class="main__figure main__fold" data-cell="">7.777,77</td>' in content
    assert '<td class="main__figure main__fold" data-cell="">5.432,10</td>' in content
    assert '<td class="text-left main__fold">Account1</td>' in content
    assert "bi-check-circle-fill" not in content

    assert f'<td class="text-left main__name">{obj2.name}</td>' not in content
    assert "6.666,66</td>" not in content


@pytest.mark.parametrize(
    "returned, closed, cells",
    [
        pytest.param(
            0,
            False,
            [(FOLDED_FIGURE, "empty", "-"), ("main__figure", "", "10,00")],
            id="nothing",
        ),
        pytest.param(
            10_00,
            True,
            [(FOLDED_FIGURE, "", "10,00"), ("main__figure", "empty", "-")],
            id="closed",
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_remaining_follows_returned_and_both_show_their_state(
    client_logged, debt_type, returned, closed, cells
):
    DEBT_FACTORIES[debt_type](price=10_00, returned=returned, closed=closed)

    content = client_logged.get(TAB_PATHS[debt_type]).content.decode("utf-8")

    assert FIGURE_CELL.findall(content) == [(FOLDED_FIGURE, "", "10,00"), *cells]


@pytest.mark.parametrize(
    "paths", [TAB_PATHS, RETURN_TAB_PATHS], ids=["debts", "returns"]
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_closed_debt_is_labelled_beside_its_name_and_by_nothing_else(
    client_logged, debt_type, paths
):
    for name, closed in (("Open name", False), ("Shut name", True)):
        debt = DEBT_FACTORIES[debt_type](name=name, closed=closed)
        RETURN_FACTORIES[debt_type](debt=debt)

    content = client_logged.get(paths[debt_type]).content.decode("utf-8")

    assert sorted(
        re.findall(r'<td class="text-left main__name">(.*?)</td>', content)
    ) == ["Open name", 'Shut name <span class="main__closed">Grąžinta</span>']
    assert ">Uždaryta</th>" not in content
    assert "bi-check-circle-fill" not in content
    assert "data-tip" not in content


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
            "Negalite uždaryti dar negrąžintos skolos.",
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


def _debt_new(debt):
    return reverse("debts:new", kwargs={"debt_type": debt.debt_type})


def _debt_update(debt):
    return reverse("debts:update", kwargs={"pk": debt.pk, "debt_type": debt.debt_type})


def _debt_delete(debt):
    return reverse("debts:delete", kwargs={"pk": debt.pk, "debt_type": debt.debt_type})


def _return_new(debt):
    return reverse("debts:return_new", kwargs={"debt_type": debt.debt_type})


def _a_return_of(debt):
    obj = RETURN_FACTORIES[debt.debt_type](debt=debt)
    return {"pk": obj.pk, "debt_type": debt.debt_type}


def _return_update(debt):
    return reverse("debts:return_update", kwargs=_a_return_of(debt))


def _return_delete(debt):
    return reverse("debts:return_delete", kwargs=_a_return_of(debt))


def _debt_data(debt):
    return {
        "date": "1999-01-01",
        "name": "New name",
        "price": "1",
        "account": debt.account.pk,
    }


def _return_data(debt):
    return {
        "date": "1999-01-02",
        "price": "1",
        "account": debt.account.pk,
        "debt": debt.pk,
    }


SAVES = [
    pytest.param(_debt_new, _debt_data, TAB_PATHS, id="debt_new"),
    pytest.param(_debt_update, _debt_data, TAB_PATHS, id="debt_update"),
    pytest.param(_return_new, _return_data, RETURN_TAB_PATHS, id="return_new"),
    pytest.param(_return_update, _return_data, RETURN_TAB_PATHS, id="return_update"),
]
DELETES = [
    pytest.param(_debt_delete, _debt_data, TAB_PATHS, id="debt_delete"),
    pytest.param(_return_delete, _return_data, RETURN_TAB_PATHS, id="return_delete"),
]


@pytest.mark.parametrize("url_of, data_of, paths", [*SAVES, *DELETES])
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_form_fires_reload(client_logged, debt_type, url_of, data_of, paths):
    debt = DEBT_FACTORIES[debt_type]()

    response = client_logged.post(
        url_of(debt), data_of(debt), headers={"HX-Request": "true"}
    )

    assert response.status_code == 204
    assert json.loads(response.headers.get("HX-Trigger", "null")) == {"reload": {}}


@pytest.mark.parametrize("url_of, data_of, paths", SAVES)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_save_without_htmx_lands_on_its_tab(
    client_logged, debt_type, url_of, data_of, paths
):
    debt = DEBT_FACTORIES[debt_type]()

    response = client_logged.post(url_of(debt), data_of(debt))

    assert response.status_code == 302
    assert response.url == paths[debt_type]
