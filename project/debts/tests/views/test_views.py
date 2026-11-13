import re
from datetime import date

import pytest
import time_machine
from django.test import Client
from django.urls import resolve, reverse

from ....accounts.tests.factories import AccountFactory
from ....bookkeeping.tests.helper import quiet_build
from ....core.tests.utils import (
    HEAD_CELL,
    PAPER_PARTS,
    count_queries,
    form_posts_to,
    nav_tabs,
    paper_page_parts,
    quick_add_pills,
    row_forms,
    tab_fragment,
)
from ...models import Debt
from ..helpers import (
    BORROW,
    DEBT_FACTORIES,
    DEBT_TYPES,
    FIGURE_CELL,
    FOLDED_FIGURE,
    LEND,
    NAME_CELL,
    RETURN_FACTORIES,
    RETURN_TAB_PATHS,
    TAB_PATHS,
)

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]

TAB_ROWS = [
    pytest.param(TAB_PATHS[LEND], DEBT_FACTORIES[LEND], "Paskolinta", id="lend"),
    pytest.param(
        RETURN_TAB_PATHS[LEND], RETURN_FACTORIES[LEND], "Grąžino", id="lend_returns"
    ),
    pytest.param(
        TAB_PATHS[BORROW], DEBT_FACTORIES[BORROW], "Pasiskolinta", id="borrow"
    ),
    pytest.param(
        RETURN_TAB_PATHS[BORROW],
        RETURN_FACTORIES[BORROW],
        "Grąžinau",
        id="borrow_returns",
    ),
]

SUBNAV = [(row.id, row.values[0]) for row in TAB_ROWS]


def test_debts_index_not_logged(client):
    url = reverse("debts:index")
    response = client.get(url)

    assert response.status_code == 302


@pytest.mark.parametrize("path, factory, title", TAB_ROWS)
@pytest.mark.parametrize(
    "headers, whole",
    [({}, True), ({"HX-Request": "true"}, False)],
    ids=["page", "fragment"],
)
def test_a_tab_is_the_whole_paper_page_unless_htmx_asks(
    client_logged, path, factory, title, headers, whole
):
    factory(remark="The year's record")

    response = client_logged.get(path, headers=headers)
    content = response.content.decode()

    assert f"<title>Skolos | {title}</title>" in content
    assert paper_page_parts(content) == dict.fromkeys(PAPER_PARTS, whole)
    assert nav_tabs(content) == (SUBNAV if whole else [])
    assert '<td class="text-left main__fold">The year&#x27;s record</td>' in content


DEBT_HEADS = [
    ("main__fold", "Suma"),
    ("main__fold", "Grąžinta"),
    ("", "Liko"),
]
RETURN_HEADS = [("", "Suma")]
TAIL_HEADS = [
    ("text-left main__fold", "Sąskaita"),
    ("text-left main__fold", "Pastaba"),
    ("edit-col", ""),
    ("delete-col", ""),
]
OTHER_PARTY = {LEND: "Paskolos gavėjas", BORROW: "Paskolos davėjas"}
OTHER_TYPE = {LEND: BORROW, BORROW: LEND}


def _a_debt(factory, name):
    factory(name=name, price=777_777, returned=543_210)


def _a_return(factory, name):
    factory(price=543_210, debt__name=name)


# the day is each factory's own date
@pytest.mark.parametrize(
    "paths, factory_table, build, heads, day, figures",
    [
        pytest.param(
            TAB_PATHS,
            DEBT_FACTORIES,
            _a_debt,
            DEBT_HEADS,
            "1999-01-01",
            [
                (FOLDED_FIGURE, "", "7.777,77"),
                (FOLDED_FIGURE, "", "5.432,10"),
                ("main__figure", "", "2.345,67"),
            ],
            id="debts",
        ),
        pytest.param(
            RETURN_TAB_PATHS,
            RETURN_FACTORIES,
            _a_return,
            RETURN_HEADS,
            "1999-01-02",
            [("main__figure", "", "5.432,10")],
            id="returns",
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_tab_draws_its_columns_and_only_its_own_records(
    client_logged, debt_type, paths, factory_table, build, heads, day, figures
):
    # both named: Faker cannot promise two different names
    build(factory_table[debt_type], "Own name")
    build(factory_table[OTHER_TYPE[debt_type]], "Other name")

    content = client_logged.get(paths[debt_type]).content.decode("utf-8")

    assert HEAD_CELL.findall(content) == [
        ("text-left", "Data"),
        ("text-left main__name", OTHER_PARTY[debt_type]),
        *heads,
        *TAIL_HEADS,
    ]
    assert f'<td class="text-left main__date">{day}</td>' in content
    assert '<td class="text-left main__name">Own name</td>' in content
    assert FIGURE_CELL.findall(content) == figures
    assert '<td class="text-left main__fold">Account1</td>' in content
    assert "Other name" not in content


def _debts_of_three_years(factory):
    factory(name="Carried", date=date(1998, 6, 1))
    factory(name="Settled", date=date(1998, 6, 1), closed=True)
    factory(name="Current", date=date(1999, 6, 1))
    factory(name="Later", date=date(2000, 6, 1))


def _returns_of_three_years(factory):
    for year, name in [(1998, "Before"), (1999, "Current"), (2000, "Later")]:
        day = date(year, 6, 1)
        factory(date=day, debt__date=day, debt__name=name)


@pytest.mark.parametrize(
    "paths, factory_table, build, shown",
    [
        pytest.param(
            TAB_PATHS,
            DEBT_FACTORIES,
            _debts_of_three_years,
            ["Carried", "Current"],
            id="debts",
        ),
        pytest.param(
            RETURN_TAB_PATHS,
            RETURN_FACTORIES,
            _returns_of_three_years,
            ["Current"],
            id="returns",
        ),
    ],
)
@pytest.mark.parametrize("debt_type", DEBT_TYPES)
def test_a_tab_lists_its_year_and_the_open_debts_before_it(
    client_logged, debt_type, paths, factory_table, build, shown
):
    build(factory_table[debt_type])

    content = client_logged.get(paths[debt_type]).content.decode("utf-8")

    assert sorted(NAME_CELL.findall(content)) == shown


@pytest.mark.parametrize(
    "path, factory", [pytest.param(*row.values[:2], id=row.id) for row in TAB_ROWS]
)
def test_a_tab_query_count_does_not_grow_with_the_rows(
    main_user, client_logged, path, factory
):
    # each Return gets its own Debt, so the rows' Debt reads grow too
    def tab_queries():
        return count_queries(lambda: tab_fragment(client_logged, path))

    with quiet_build(main_user):
        factory.create_batch(2)
    two = tab_queries()

    with quiet_build(main_user):
        factory.create_batch(4)
    six = tab_queries()

    assert six == two


@pytest.mark.parametrize(
    "path, other_factory",
    [
        pytest.param(TAB_PATHS[LEND], DEBT_FACTORIES[BORROW], id="lend"),
        pytest.param(
            RETURN_TAB_PATHS[LEND], RETURN_FACTORIES[BORROW], id="lend_returns"
        ),
        pytest.param(TAB_PATHS[BORROW], DEBT_FACTORIES[LEND], id="borrow"),
        pytest.param(
            RETURN_TAB_PATHS[BORROW], RETURN_FACTORIES[LEND], id="borrow_returns"
        ),
    ],
)
def test_a_tab_with_no_records_of_its_own_says_so(client_logged, path, other_factory):
    other_factory(price=666)

    content = client_logged.get(path).content.decode("utf-8")

    assert re.search(
        r'<div class="alert">\s*1999 metais įrašų nėra\.\s*</div>', content
    )


@pytest.mark.parametrize(
    "path, factory, debt_type, update, delete",
    [
        pytest.param(
            TAB_PATHS[LEND],
            DEBT_FACTORIES[LEND],
            LEND,
            "debts:update",
            "debts:delete",
            id="lend",
        ),
        pytest.param(
            RETURN_TAB_PATHS[LEND],
            RETURN_FACTORIES[LEND],
            LEND,
            "debts:return_update",
            "debts:return_delete",
            id="lend_returns",
        ),
        pytest.param(
            TAB_PATHS[BORROW],
            DEBT_FACTORIES[BORROW],
            BORROW,
            "debts:update",
            "debts:delete",
            id="borrow",
        ),
        pytest.param(
            RETURN_TAB_PATHS[BORROW],
            RETURN_FACTORIES[BORROW],
            BORROW,
            "debts:return_update",
            "debts:return_delete",
            id="borrow_returns",
        ),
    ],
)
def test_a_tab_row_offers_its_edit_and_delete_buttons(
    client_logged, path, factory, debt_type, update, delete
):
    obj = factory()

    content = client_logged.get(path).content.decode("utf-8")

    kwargs = {"pk": obj.pk, "debt_type": debt_type}
    assert row_forms(content) == [
        (
            reverse(update, kwargs=kwargs),
            [
                ("edit-col", reverse(update, kwargs=kwargs)),
                ("delete-col", reverse(delete, kwargs=kwargs)),
            ],
        )
    ]


def test_quick_add_offers_a_pill_per_tab(client_logged):
    content = client_logged.get(TAB_PATHS[LEND]).content.decode()

    assert quick_add_pills(content) == [
        ("button", "lend", 'hx-get="/debts/lend/new/"', "Paskolinti"),
        (
            "button",
            "lend_returns",
            'hx-get="/debts/lend/return/new/"',
            "Pridėti grąžinimą",
        ),
        ("button", "borrow", 'hx-get="/debts/borrow/new/"', "Pasiskolinti"),
        (
            "button",
            "borrow_returns",
            'hx-get="/debts/borrow/return/new/"',
            "Pridėti grąžinimą",
        ),
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
            BORROW,
            DEBT_FACTORIES[BORROW],
            "debts:update",
            1,
            "Borrow Remark",
            "Skola",
            id="debt-borrow",
        ),
        pytest.param(
            LEND,
            DEBT_FACTORIES[LEND],
            "debts:update",
            1,
            "Lend Remark",
            "Skola",
            id="debt-lend",
        ),
        pytest.param(
            BORROW,
            RETURN_FACTORIES[BORROW],
            "debts:return_update",
            2,
            "Borrow Return Remark",
            "Skolos grąžinimas",
            id="return-borrow",
        ),
        pytest.param(
            LEND,
            RETURN_FACTORIES[LEND],
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


def _closed_debts_return(debt_type, _second_user):
    debt = DEBT_FACTORIES[debt_type](closed=True)
    obj = RETURN_FACTORIES[debt_type](debt=debt, price=666)
    return obj, {
        "date": "1999-1-2",
        "price": "1",
        "account": obj.account.pk,
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
        *(
            pytest.param(_closed_debts_return, url_name, send, id=f"closed_{id_}")
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
