from datetime import date

import pytest
import time_machine
from django.test import Client
from django.urls import resolve, reverse

from ....accounts.tests.factories import AccountFactory
from ....bookkeeping.tests.helper import quiet_build
from ....core.tests.utils import (
    PAPER_PARTS,
    count_queries,
    form_posts_to,
    paper_page_parts,
    quick_add_pills,
    tab_fragment,
)
from ...models import Debt
from .. import factories
from ..helpers import DEBT_FACTORIES, DEBT_TYPES, RETURN_FACTORIES, TAB_PATHS

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]

TAB_TITLES = {Debt.DebtType.LEND: "Paskolinta", Debt.DebtType.BORROW: "Pasiskolinta"}


def test_debts_index_not_logged(client):
    url = reverse("debts:index")
    response = client.get(url)

    assert response.status_code == 302


@pytest.mark.parametrize("debt_type", TAB_PATHS)
@pytest.mark.parametrize(
    "headers, whole",
    [({}, True), ({"HX-Request": "true"}, False)],
    ids=["page", "fragment"],
)
def test_a_debt_tab_is_the_whole_paper_page_unless_htmx_asks(
    client_logged, debt_type, headers, whole
):
    DEBT_FACTORIES[debt_type](remark="The year's debt")

    response = client_logged.get(TAB_PATHS[debt_type], headers=headers)
    content = response.content.decode()

    assert f"<title>Skolos | {TAB_TITLES[debt_type]}</title>" in content
    assert paper_page_parts(content) == dict.fromkeys(PAPER_PARTS, whole)
    assert '<td class="text-left main__fold">The year&#x27;s debt</td>' in content


@pytest.mark.parametrize("debt_type", TAB_PATHS)
def test_a_debt_tab_query_count_does_not_grow_with_the_rows(
    main_user, client_logged, debt_type
):
    def tab_queries():
        return count_queries(lambda: tab_fragment(client_logged, TAB_PATHS[debt_type]))

    with quiet_build(main_user):
        DEBT_FACTORIES[debt_type].create_batch(2)
    two = tab_queries()

    with quiet_build(main_user):
        DEBT_FACTORIES[debt_type].create_batch(4)
    six = tab_queries()

    assert six == two


def test_quick_add_offers_a_pill_per_debt_type(client_logged):
    content = client_logged.get("/debts/").content.decode()

    assert quick_add_pills(content) == [
        ("button", "lend", 'hx-get="/debts/lend/new/"', "Paskolinti"),
        ("button", "borrow", 'hx-get="/debts/borrow/new/"', "Pasiskolinti"),
    ]


@pytest.mark.parametrize(
    "url_name, title",
    [
        pytest.param("debts:new", "Skola", id="debt"),
        pytest.param("debts:return_new", "Skolos grąžinimas", id="return"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
@time_machine.travel("2000-01-01")
def test_a_new_form_opens_on_the_selected_year(
    client_logged, debt_type, url_name, title
):
    url = reverse(url_name, kwargs={"debt_type": debt_type})
    content = client_logged.get(url).content.decode()

    assert '<input type="text" name="date" value="1999-01-01"' in content
    assert form_posts_to(content, "generic-form", url)
    assert f'<h5 class="modal-title">{title}</h5>' in content


@pytest.mark.parametrize(
    "url_name, data, fields",
    [
        pytest.param(
            "debts:new",
            {"date": "x", "name": "A", "price": "0"},
            ["account", "date", "name", "price"],
            id="debt",
        ),
        pytest.param(
            "debts:return_new",
            {"debt": "A", "price": "0"},
            ["account", "date", "debt", "price"],
            id="return",
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_new_form_with_invalid_data_names_each_field(
    client_logged, debt_type, url_name, data, fields
):
    url = reverse(url_name, kwargs={"debt_type": debt_type})
    response = client_logged.post(url, data)

    assert sorted(response.context["form"].errors) == fields


@pytest.mark.parametrize(
    "debt_type, factory, url_name, day, remark, title",
    [
        pytest.param(
            Debt.DebtType.BORROW,
            factories.BorrowFactory,
            "debts:update",
            1,
            "Borrow Remark",
            "Skola",
            id="debt-borrow",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            factories.LendFactory,
            "debts:update",
            1,
            "Lend Remark",
            "Skola",
            id="debt-lend",
        ),
        pytest.param(
            Debt.DebtType.BORROW,
            factories.BorrowReturnFactory,
            "debts:return_update",
            2,
            "Borrow Return Remark",
            "Skolos grąžinimas",
            id="return-borrow",
        ),
        pytest.param(
            Debt.DebtType.LEND,
            factories.LendReturnFactory,
            "debts:return_update",
            2,
            "Lend Return Remark",
            "Skolos grąžinimas",
            id="return-lend",
        ),
    ],
)
def test_an_update_form_holds_the_record(
    client_logged, debt_type, factory, url_name, day, remark, title
):
    obj = factory(price=1)
    url = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, day)
    assert form.instance.price == 0.01
    assert form.instance.account.title == "Account1"
    assert form.instance.remark == remark
    content = response.content.decode()
    assert form_posts_to(content, "generic-form", url)
    assert f'<h5 class="modal-title">{title}</h5>' in content


RECORDS = {"debt": DEBT_FACTORIES, "return": RETURN_FACTORIES}


@pytest.mark.parametrize(
    "record, url_name, title",
    [
        pytest.param("debt", "debts:delete", "Trinti skolą", id="debt"),
        pytest.param(
            "return", "debts:return_delete", "Trinti skolos grąžinimą", id="return"
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_delete_form_names_the_record(
    client_logged, debt_type, record, url_name, title
):
    obj = RECORDS[record][debt_type]()

    url = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})
    content = client_logged.get(url).content.decode("utf-8")

    assert form_posts_to(content, "delete-form", url)
    assert f"Ar tikrai norite ištrinti: <strong>{obj}</strong>?" in content
    assert f'<h5 class="modal-title">{title}</h5>' in content


@pytest.mark.parametrize(
    "record, url_name",
    [
        pytest.param("debt", "debts:delete", id="debt"),
        pytest.param("return", "debts:return_delete", id="return"),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_delete_removes_the_record(client_logged, debt_type, record, url_name):
    obj = RECORDS[record][debt_type]()

    url = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = client_logged.post(url)

    assert response.status_code == 204
    assert not type(obj).objects.filter(pk=obj.pk).exists()


def _other_journals_account(second_user):
    # a title of its own, or AccountFactory gets the first journal's account back
    return AccountFactory(journal=second_user.journal, title="a2")


def _other_journals_debt(debt_type, second_user):
    account = _other_journals_account(second_user)
    debt = DEBT_FACTORIES[debt_type](
        name="yyy", price=666, journal=second_user.journal, account=account
    )
    return debt, {
        "name": "zzz",
        "price": "1",
        "date": "1999-12-31",
        "account": account.pk,
    }


def _other_journals_return(debt_type, second_user):
    account = _other_journals_account(second_user)
    debt = DEBT_FACTORIES[debt_type](account=account, journal=second_user.journal)
    obj = RETURN_FACTORIES[debt_type](debt=debt, account=account, price=666)
    return obj, {
        "date": "1999-1-2",
        "price": "1",
        "account": account.pk,
        "debt": debt.pk,
    }


DEBT_SENDS = [
    ("debts:update", Client.get, "update_get"),
    ("debts:update", Client.post, "update_post"),
    ("debts:delete", Client.get, "delete_get"),
    ("debts:delete", Client.post, "delete_post"),
]
RETURN_SENDS = [
    ("debts:return_update", Client.get, "update_get"),
    ("debts:return_update", Client.post, "update_post"),
    ("debts:return_delete", Client.get, "delete_get"),
    ("debts:return_delete", Client.post, "delete_post"),
]


@pytest.mark.parametrize(
    "build, url_name, send",
    [
        *(
            pytest.param(_other_journals_debt, url_name, send, id=f"debt_{id_}")
            for url_name, send, id_ in DEBT_SENDS
        ),
        *(
            pytest.param(_other_journals_return, url_name, send, id=f"return_{id_}")
            for url_name, send, id_ in RETURN_SENDS
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_record_out_of_reach_is_404(
    client_logged, second_user, debt_type, build, url_name, send
):
    obj, data = build(debt_type, second_user)

    url = reverse(url_name, kwargs={"pk": obj.pk, "debt_type": debt_type})
    response = send(client_logged, url, data)

    assert response.status_code == 404
    assert type(obj).objects.get(pk=obj.pk).price == 666


@pytest.mark.parametrize(
    "send, path",
    [
        pytest.param(Client.get, "/debts/x/new/", id="new"),
        pytest.param(Client.post, "/debts/x/new/", id="create"),
        pytest.param(Client.get, "/debts/x/return/lists/", id="return_list"),
    ],
)
def test_debts_url_of_an_unknown_type_is_404(client_logged, send, path):
    response = send(client_logged, path, {"name": "Name", "price": "1"})

    assert response.status_code == 404
    assert not Debt.objects.exists()


@pytest.mark.parametrize("debt_type", Debt.DebtType)
def test_debts_url_resolves_the_type_to_the_enum(debt_type):
    match = resolve(reverse("debts:new", kwargs={"debt_type": debt_type.value}))

    assert type(match.kwargs["debt_type"]) is Debt.DebtType
    assert match.kwargs["debt_type"] == debt_type
