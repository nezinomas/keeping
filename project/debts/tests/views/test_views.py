import pytest
from django.test import Client
from django.urls import resolve, reverse

from ....bookkeeping.tests.helper import quiet_build
from ....core.tests.utils import (
    PAPER_PARTS,
    count_queries,
    paper_page_parts,
    quick_add_pills,
    tab_fragment,
)
from ...models import Debt
from ..helpers import DEBT_FACTORIES, TAB_PATHS

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
