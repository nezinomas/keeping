import json
import re
from datetime import date

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....core.tests.utils import count_queries, edit_row_opening
from ... import models
from ...services.model_services import DebtModelService
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES, TAB_PATHS

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


@pytest.mark.parametrize(
    "debt_type, other_factory",
    [
        pytest.param(models.Debt.DebtType.BORROW, factories.LendFactory, id="borrow"),
        pytest.param(models.Debt.DebtType.LEND, factories.BorrowFactory, id="lend"),
    ],
)
def test_debt_tab_empty(client_logged, debt_type, other_factory):
    other_factory(price=666)

    response = client_logged.get(TAB_PATHS[debt_type])
    content = response.content.decode("utf-8")

    assert re.search(
        r'<div class="alert">\s*1999 metais įrašų nėra\.\s*</div>', content
    )


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
    assert '">Uždaryta</th>' in content
    assert '<th class="edit-col"></th>' in content
    assert '<th class="delete-col"></th>' in content

    assert '<td class="text-left main__date">1999-01-01</td>' in content
    assert f'<td class="text-left main__name">{obj1.name}</td>' in content
    assert '<td class="main__figure" data-cell="">7.777,77</td>' in content
    assert re.search(
        r'<td class="main__figure" data-cell="">\s*<span>\s*5\.432,10\s*</span>',
        content,
    )
    assert '<td class="text-left main__fold">Account1</td>' in content
    assert (
        '<td class="text-center"><i class="bi bi-check-circle-fill"></i></td>'
        in content
    )

    assert f'<td class="text-left main__name">{obj2.name}</td>' not in content
    assert '<td class="main__figure" data-cell="">6.666,66</td>' not in content


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_an_open_debts_returned_cell_tips_its_remaining(client_logged, debt_type):
    DEBT_FACTORIES[debt_type](price=10_00, returned=4_00)

    content = client_logged.get(TAB_PATHS[debt_type]).content.decode("utf-8")

    assert re.search(
        r'<td class="main__figure" data-cell="">\s*'
        r'<span\s+class="tip right w100" data-tip="Liko grąžinti:  6,00">\s*4,00\s*',
        content,
    )


@pytest.mark.parametrize("url_name", ["debts:update", "debts:delete"])
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_debt_tab_links_each_row_button(client_logged, debt_type, url_name):
    obj = DEBT_FACTORIES[debt_type]()

    response = client_logged.get(TAB_PATHS[debt_type])
    content = response.content.decode("utf-8")

    link = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})

    assert f'<a role="button" hx-get="{link}"' in content


@pytest.mark.parametrize(
    "url_name, debt_type, factory",
    [
        # each return gets its own debt, so the rows' debt reads grow too
        pytest.param(
            "debts:return_list",
            "borrow",
            factories.BorrowReturnFactory,
            id="borrow-return",
        ),
        pytest.param(
            "debts:return_list", "lend", factories.LendReturnFactory, id="lend-return"
        ),
    ],
)
def test_list_query_count_does_not_grow_with_the_rows(
    client_logged, url_name, debt_type, factory
):
    url = reverse(url_name, kwargs={"debt_type": debt_type})
    factory.create_batch(2)
    two = count_queries(lambda: client_logged.get(url))

    factory.create_batch(4)
    six = count_queries(lambda: client_logged.get(url))

    assert six == two


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


@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_debt_row_opens_its_update_form(client_logged, debt_type):
    obj = DEBT_FACTORIES[debt_type]()

    content = client_logged.get(TAB_PATHS[debt_type]).content.decode("utf-8")

    update = reverse("debts:update", kwargs={"pk": obj.pk, "debt_type": debt_type})
    assert edit_row_opening(update) in content


def _debt_new(debt):
    return reverse("debts:new", kwargs={"debt_type": debt.debt_type})


def _debt_update(debt):
    return reverse("debts:update", kwargs={"pk": debt.pk, "debt_type": debt.debt_type})


def _debt_delete(debt):
    return reverse("debts:delete", kwargs={"pk": debt.pk, "debt_type": debt.debt_type})


def _debt_data(debt):
    return {
        "date": "1999-01-01",
        "name": "New name",
        "price": "1",
        "account": debt.account.pk,
    }


DEBT_SAVES = [
    pytest.param(_debt_new, id="new"),
    pytest.param(_debt_update, id="update"),
]


@pytest.mark.parametrize(
    "url_of", [*DEBT_SAVES, pytest.param(_debt_delete, id="delete")]
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_debt_form_fires_reload(client_logged, debt_type, url_of):
    debt = DEBT_FACTORIES[debt_type]()

    response = client_logged.post(
        url_of(debt), _debt_data(debt), headers={"HX-Request": "true"}
    )

    assert response.status_code == 204
    assert json.loads(response.headers.get("HX-Trigger", "null")) == {"reload": {}}


@pytest.mark.parametrize("url_of", DEBT_SAVES)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_debt_save_without_htmx_lands_on_its_tab(client_logged, debt_type, url_of):
    debt = DEBT_FACTORIES[debt_type]()

    response = client_logged.post(url_of(debt), _debt_data(debt))

    assert response.status_code == 302
    assert response.url == TAB_PATHS[debt_type]
