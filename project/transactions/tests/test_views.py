import json
import re
from datetime import date
from functools import partial
from typing import NamedTuple

import pytest
import time_machine
from django.forms.models import model_to_dict
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...bookkeeping.tests.helper import quiet_build
from ...core.tests.utils import (
    clean_content,
    count_queries,
    nav_tabs,
    quick_add_pills,
    view_for,
)
from ...savings.models import SavingBalance, SavingType
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from ...users.views import Login
from .. import models, views
from ..tabs import TABS
from .factories import SavingChangeFactory, SavingCloseFactory, TransactionFactory

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


class Kind(NamedTuple):
    factory: type
    model: type
    to_factory: type
    from_factory: type
    new_url: str
    update_url: str
    delete_url: str
    to_title: str
    delete_text: str
    from_title: str
    modal_title: str
    tab_url: str


KINDS = {
    "transactions": Kind(
        TransactionFactory,
        models.Transaction,
        AccountFactory,
        AccountFactory,
        "transactions:new",
        "transactions:update",
        "transactions:delete",
        "Account2",
        "1999-01-01 Account1 -&gt; Account2: 2,00",
        "Account1",
        "Pinigų pervedimas",
        "transactions:index",
    ),
    "savings_close": Kind(
        SavingCloseFactory,
        models.SavingClose,
        AccountFactory,
        SavingTypeFactory,
        "transactions:savings_close_new",
        "transactions:savings_close_update",
        "transactions:savings_close_delete",
        "Account To",
        "1999-01-01 Savings From -&gt; Account To: 0,10",
        "Savings From",
        "Fondas ⇒ Sąskaita",
        "transactions:tab_sales",
    ),
    "savings_change": Kind(
        SavingChangeFactory,
        models.SavingChange,
        SavingTypeFactory,
        SavingTypeFactory,
        "transactions:savings_change_new",
        "transactions:savings_change_update",
        "transactions:savings_change_delete",
        "Savings To",
        "1999-01-01 Savings From -&gt; Savings To: 0,10",
        "Savings From",
        "Fondas ⇔ Fondas",
        "transactions:tab_switches",
    ),
}
by_kind = pytest.mark.parametrize("kind", KINDS.values(), ids=KINDS.keys())
by_fund_move = pytest.mark.parametrize(
    "kind",
    [KINDS["savings_close"], KINDS["savings_change"]],
    ids=["savings_close", "savings_change"],
)
CHECKED_BOX = re.compile(r'<input type="checkbox" .*? checked>')
STICKY_HEADERS = r'<script nonce="[^"]*" src="/static/js/sticky-table-headers.js">'


TAB_TITLES = {
    "transactions": "Pervedimai",
    "sales": "Fondų pardavimai",
    "switches": "Fondų keitimai",
    "accounts": "Sąskaitos",
}


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
@pytest.mark.parametrize(
    "headers, whole",
    [({}, True), ({"HX-Request": "true"}, False)],
    ids=["page", "fragment"],
)
def test_a_tab_is_the_whole_paper_page_unless_htmx_asks(
    client_logged, tab, headers, whole
):
    content = client_logged.get(tab.url, headers=headers).content.decode()

    assert f"<title>Pervedimai | {TAB_TITLES[tab.name]}</title>" in content
    assert (
        '<link rel="stylesheet" href="/static/css/paper.min.css">' in content
    ) is whole
    assert ('<nav class="subnav">' in content) is whole
    assert bool(re.search(r'<div\b[^>]*class="quick-add\b', content)) is whole
    assert bool(re.search(STICKY_HEADERS, content)) is whole


# each move out of an owner of its own, so a read per owner grows with the rows
A_MOVE_OUT_OF = {
    "transactions": lambda i: TransactionFactory(
        from_account=AccountFactory(title=f"F{i}")
    ),
    "sales": lambda i: SavingCloseFactory(
        from_account=SavingTypeFactory(title=f"F{i}", closed=1999)
    ),
    "switches": lambda i: SavingChangeFactory(
        from_account=SavingTypeFactory(title=f"F{i}", closed=1999)
    ),
    "accounts": lambda i: AccountFactory(title=f"F{i}"),
}


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_query_count_does_not_grow_with_the_rows(client_logged, tab):
    a_move_out_of = A_MOVE_OUT_OF[tab.name]

    def tab_queries():
        return count_queries(
            lambda: client_logged.get(tab.url, headers={"HX-Request": "true"})
        )

    for i in range(2):
        a_move_out_of(i)
    two = tab_queries()

    for i in range(2, 6):
        a_move_out_of(i)
    six = tab_queries()

    assert six == two


def _transactions_tab(client):
    return client.get(
        reverse("transactions:tab_transactions"), headers={"HX-Request": "true"}
    ).content.decode()


def test_transactions_tab_lists_the_years_transactions_newest_first(
    client_logged, second_user
):
    TransactionFactory(date=date(1999, 1, 5), from_account=AccountFactory(title="A"))
    TransactionFactory(
        date=date(1999, 3, 9), price=100_000_000, from_account=AccountFactory(title="B")
    )
    TransactionFactory(date=date(1999, 3, 2), from_account=AccountFactory(title="C"))
    _foreign_move(KINDS["transactions"], second_user.journal)

    content = _transactions_tab(client_logged)

    assert '<table class="main striped hover sticky-table">' in content
    assert re.findall(r'<th class="([^"]*)">([^<]*)</th>', content) == [
        ("text-left", "Data"),
        ("text-left", "Iš sąskaitos"),
        ("text-left", "Į sąskaitą"),
        ("price-col", "Suma"),
        ("edit-col", ""),
        ("delete-col", ""),
    ]
    rows = re.findall(
        r'<tr [^>]*class="([^"]*)">\s*<td class="text-left main__date">([^<]*)</td>'
        r'\s*<td class="text-left">([^<]*)</td>\s*<td class="text-left">([^<]*)</td>'
        r'\s*<td class="main__figure">([^<]*)</td>',
        content,
    )
    assert rows == [
        ("", "1999-03-09", "B", "Account2", "1.000.000,00"),
        ("", "1999-03-02", "C", "Account2", "2,00"),
        ("table-group-divider", "1999-01-05", "A", "Account2", "2,00"),
    ]


def _fund_moves(second_user):
    bank = AccountFactory(title="Bank")
    sold = SavingTypeFactory(title="Sold", closed=1999)
    tied = SavingTypeFactory(title="Tied", closed=1999)
    early = SavingTypeFactory(title="Early", closed=1999)
    later = SavingTypeFactory(title="Later", closed=2000)
    other = SavingTypeFactory(title="Other")
    sale = partial(SavingCloseFactory, to_account=bank, price=100_000_000, fee=100_000)
    switch = partial(SavingChangeFactory, to_account=other)

    sale(from_account=sold, date=date(1999, 6, 1))
    switch(from_account=sold, date=date(1999, 4, 1))
    sale(from_account=tied, date=date(1999, 3, 1))
    switch(from_account=tied, date=date(1999, 3, 1))
    sale(from_account=early, date=date(1999, 1, 1))
    switch(from_account=early, date=date(1999, 2, 1))
    sale(from_account=later, date=date(2000, 1, 1))
    switch(from_account=later, date=date(2000, 1, 1))
    _foreign_move(KINDS["savings_close"], second_user.journal)
    _foreign_move(KINDS["savings_change"], second_user.journal)


CLOSED = ' <span class="main__mark">Uždaryta</span>'


# the Fund's last move in its Close year is marked, a same-day pair both, an earlier
# move of either kind not; the to-fund never
@pytest.mark.parametrize(
    "url_name, to_header, rows",
    [
        pytest.param(
            "transactions:tab_sales",
            "Į sąskaitą",
            [
                ("", "1999-06-01", f"Sold{CLOSED}", "Bank", "1.000.000,00", "1.000,00"),
                ("table-group-divider", "1999-03-01", f"Tied{CLOSED}", "Bank")
                + ("1.000.000,00", "1.000,00"),
                ("table-group-divider", "1999-01-01", "Early", "Bank")
                + ("1.000.000,00", "1.000,00"),
            ],
            id="sales",
        ),
        pytest.param(
            "transactions:tab_switches",
            "Į fondą",
            [
                ("", "1999-04-01", "Sold", "Other", "0,10", "0,02"),
                ("table-group-divider", "1999-03-01", f"Tied{CLOSED}", "Other")
                + ("0,10", "0,02"),
                ("table-group-divider", "1999-02-01", f"Early{CLOSED}", "Other")
                + ("0,10", "0,02"),
            ],
            id="switches",
        ),
    ],
)
def test_a_fund_tab_lists_the_years_moves_newest_first_marking_the_close(
    client_logged, second_user, url_name, to_header, rows
):
    _fund_moves(second_user)

    content = client_logged.get(
        reverse(url_name), headers={"HX-Request": "true"}
    ).content.decode()

    assert '<table class="main striped hover sticky-table">' in content
    assert re.findall(r'<th class="([^"]*)">([^<]*)</th>', content) == [
        ("text-left", "Data"),
        ("text-left", "Iš fondo"),
        ("text-left", to_header),
        ("price-col", "Suma"),
        ("price-col", "Mokesčiai"),
        ("edit-col", ""),
        ("delete-col", ""),
    ]
    assert (
        re.findall(
            r'<tr [^>]*class="([^"]*)">\s*<td class="text-left main__date">([^<]*)</td>'
            r'\s*<td class="text-left">(.*?)</td>\s*<td class="text-left">(.*?)</td>'
            r'\s*<td class="main__figure">([^<]*)</td>'
            r'\s*<td class="main__figure">([^<]*)</td>',
            content,
        )
        == rows
    )


OPEN_URL = "/transactions/accounts/open/"
ALL_URL = "/transactions/accounts/all/"
OPEN_IN_2022 = ["Zeta", "Alpha", "Beta", "Edge"]


# viewing 2022: open is closed empty or in 2022 or later, in order then title; closed
# before 2022 is struck, captioned and last, by close year then title; "All" is junk
@pytest.mark.parametrize(
    "scope, filter_line, rows, tab_url",
    [
        pytest.param(
            "open",
            [(" aria-current", OPEN_URL, "Atidarytos"), ("", ALL_URL, "Visos")],
            OPEN_IN_2022,
            OPEN_URL,
            id="open",
        ),
        pytest.param(
            "all",
            [("", OPEN_URL, "Atidarytos"), (" aria-current", ALL_URL, "Visos")],
            [
                *OPEN_IN_2022,
                '<s>Young</s> <span class="main__closed">uždaryta 2019</span>',
                '<s>Ancient</s> <span class="main__closed">uždaryta 2021</span>',
                '<s>Old</s> <span class="main__closed">uždaryta 2021</span>',
            ],
            ALL_URL,
            id="all",
        ),
        pytest.param(
            "All",
            [(" aria-current", OPEN_URL, "Atidarytos"), ("", ALL_URL, "Visos")],
            OPEN_IN_2022,
            OPEN_URL,
            id="junk",
        ),
    ],
)
def test_the_accounts_tab_lists_its_scope_in_order(
    client_logged, main_user, second_user, scope, filter_line, rows, tab_url
):
    main_user.year = 2022
    main_user.save()
    AccountFactory(title="Zeta", order=1)
    AccountFactory(title="Beta", order=2, closed=2024)
    AccountFactory(title="Alpha", order=2)
    AccountFactory(title="Edge", order=3, closed=2022)
    AccountFactory(title="Old", order=1, closed=2021)
    AccountFactory(title="Young", order=1, closed=2019)
    AccountFactory(title="Ancient", order=3, closed=2021)
    AccountFactory(title="Foreign", order=1, journal=second_user.journal)

    content = client_logged.get(
        reverse("transactions:tab_accounts", args=[scope])
    ).content.decode()

    assert (
        re.findall(
            r'<button type="button" class="filter-line__item"( aria-current)?[^>]*'
            r' hx-get="([^"]*)" hx-push-url="true" hx-target="#tab_content">'
            r"([^<]*)</button>",
            content,
        )
        == filter_line
    )
    assert '<table class="main striped hover">' in content
    assert re.findall(r'<th class="([^"]*)">([^<]*)</th>', content) == [
        ("text-left", "Sąskaita"),
        ("edit-col", ""),
    ]
    assert (
        re.findall(
            r'<tr hx-get="[^"]*" hx-trigger="dblclick" hx-target="#mainModal">\s*'
            r'<td class="text-left">(.*?)</td>',
            content,
        )
        == rows
    )
    assert re.findall(
        r'<div hx-get="([^"]*)" hx-target="#tab_content" hx-trigger="reload', content
    ) == [tab_url]


def test_a_scope_with_no_accounts_draws_the_notice_under_the_filter_line(
    client_logged,
):
    AccountFactory(title="Old", closed=1998)

    content = client_logged.get(
        reverse("transactions:tab_accounts", args=["open"]),
        headers={"HX-Request": "true"},
    ).content.decode()

    assert re.search(
        r'<nav class="filter-line".*</nav>\s*<div class="alert">\s*'
        r"1999 metais įrašų nėra.\s*</div>",
        content,
        re.DOTALL,
    )


def test_an_account_row_opens_its_form(client_logged):
    account = AccountFactory(title="Bank")

    content = client_logged.get(
        reverse("transactions:tab_accounts", args=["open"]),
        headers={"HX-Request": "true"},
    ).content.decode()

    rows = re.findall(
        r'<tr hx-get="([^"]*)" hx-trigger="dblclick" hx-target="#mainModal"'
        r'.*?<td class="edit-col">\s*<a role="button" hx-get="([^"]*)"',
        content,
        re.DOTALL,
    )
    update = reverse("accounts:update", args=[account.pk])
    assert rows == [(update, update)]


@by_kind
def test_a_move_row_opens_its_own_forms(client_logged, kind):
    move = kind.factory()

    content = client_logged.get(
        reverse(kind.tab_url), headers={"HX-Request": "true"}
    ).content.decode()

    rows = re.findall(
        r'<tr hx-get="([^"]*)" hx-trigger="dblclick" hx-target="#mainModal"'
        r'.*?<td class="edit-col">\s*<a role="button" hx-get="([^"]*)"'
        r'.*?<td class="delete-col">\s*<a role="button" hx-get="([^"]*)"',
        content,
        re.DOTALL,
    )
    update = reverse(kind.update_url, args=[move.pk])
    assert rows == [(update, update, reverse(kind.delete_url, args=[move.pk]))]


@by_kind
def test_a_tab_on_an_empty_year_draws_the_paper_notice(client_logged, kind):
    kind.factory(date=date(2000, 1, 1))

    content = client_logged.get(
        reverse(kind.tab_url), headers={"HX-Request": "true"}
    ).content.decode()

    assert re.search(r'<div class="alert">\s*1999 metais įrašų nėra.\s*</div>', content)
    assert "<b>" not in content


def test_quick_add_offers_its_pill(client_logged):
    content = client_logged.get(reverse("transactions:index")).content.decode()

    assert quick_add_pills(content) == [
        ("button", "transactions", 'hx-get="/transactions/new/"', "Pridėti pervedimą"),
        ("button", "sales", 'hx-get="/savings_close/new/"', "Pridėti pardavimą"),
        ("button", "switches", 'hx-get="/savings_change/new/"', "Pridėti keitimą"),
        ("button", "accounts", 'hx-get="/accounts/new/"', "Pridėti sąskaitą"),
    ]


def test_nav_offers_every_tab(client_logged):
    content = client_logged.get(reverse("transactions:index")).content.decode()

    assert nav_tabs(content) == [
        ("transactions", "/transactions/"),
        ("sales", "/transactions/sales/"),
        ("switches", "/transactions/switches/"),
        ("accounts", "/transactions/accounts/open/"),
    ]


def _move_form_data(move):
    return {
        "date": "1999-01-01",
        "price": "1",
        "from_account": move.from_account.pk,
        "to_account": move.to_account.pk,
    }


SAVES = [
    pytest.param(lambda kind, move: reverse(kind.new_url), _move_form_data, id="new"),
    pytest.param(
        lambda kind, move: reverse(kind.update_url, kwargs={"pk": move.pk}),
        _move_form_data,
        id="update",
    ),
]
DELETE = pytest.param(
    lambda kind, move: reverse(kind.delete_url, kwargs={"pk": move.pk}),
    lambda move: {},
    id="delete",
)


@by_kind
@pytest.mark.parametrize("url_of, data_of", [*SAVES, DELETE])
def test_a_move_form_fires_reload(client_logged, kind, url_of, data_of):
    move = kind.factory()

    response = client_logged.post(
        url_of(kind, move), data_of(move), headers={"HX-Request": "true"}
    )

    assert json.loads(response.headers.get("HX-Trigger", "null")) == {"reload": {}}


# a delete answers 204 either way
@by_kind
@pytest.mark.parametrize("url_of, data_of", SAVES)
def test_a_move_save_without_htmx_lands_on_its_tab(
    client_logged, kind, url_of, data_of
):
    move = kind.factory()

    response = client_logged.post(url_of(kind, move), data_of(move))

    assert response.url == reverse(kind.tab_url)


@by_kind
@time_machine.travel("2000-01-01")
def test_load_form(client_logged, kind):
    url = reverse(kind.new_url)
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert url in actual
    assert f'<h5 class="modal-title">{kind.modal_title}</h5>' in actual


def _post_new(client_logged, kind, **extra):
    a_from = kind.from_factory(title="From")
    a_to = kind.to_factory(title="To")
    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "from_account": a_from.pk,
        "to_account": a_to.pk,
    } | extra

    client_logged.post(reverse(kind.new_url), data)

    return kind.model.objects.get(), a_from, a_to


def _assert_saved(actual, a_from, a_to):
    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.from_account == a_from
    assert actual.to_account == a_to


# a Transaction has no Fee; a fund move's posted Fee is stored in cents, none as 0
by_fee = pytest.mark.parametrize(
    "kind, posted, fee",
    [
        pytest.param(KINDS["transactions"], {}, {}, id="transactions"),
        pytest.param(
            KINDS["savings_close"], {"fee": "0.01"}, {"fee": 1}, id="savings_close-fee"
        ),
        pytest.param(KINDS["savings_close"], {}, {"fee": 0}, id="savings_close-no_fee"),
        pytest.param(
            KINDS["savings_change"],
            {"fee": "0.01"},
            {"fee": 1},
            id="savings_change-fee",
        ),
        pytest.param(
            KINDS["savings_change"], {}, {"fee": 0}, id="savings_change-no_fee"
        ),
    ],
)


@by_fee
def test_save(client_logged, kind, posted, fee):
    actual, a_from, a_to = _post_new(client_logged, kind, **posted)

    _assert_saved(actual, a_from, a_to)
    assert model_to_dict(actual, fields=fee) == fee


@by_kind
def test_save_invalid_data(client_logged, kind):
    data = {
        "date": "x",
        "price": "x",
        "from_account": 0,
        "to_account": 0,
    }

    response = client_logged.post(reverse(kind.new_url), data)
    actual = response.content.decode("utf-8")

    assert kind.model.objects.count() == 0
    assert actual.count('aria-invalid="true"') == 4


@pytest.mark.parametrize(
    "kind, kwargs, more",
    [
        pytest.param(
            KINDS["transactions"],
            {"price": 1},
            ('<option value="{to}">Account2</option>',),
            id="transactions",
        ),
        pytest.param(
            KINDS["savings_close"],
            {"price": 1, "fee": 1},
            ('name="fee" value="0.01"',),
            id="savings_close",
        ),
        pytest.param(
            KINDS["savings_change"],
            {"price": 1, "fee": 1},
            ('name="fee" value="0.01"', '<option value="{to}">Savings To</option>'),
            id="savings_change",
        ),
    ],
)
def test_load_update_form(client_logged, kind, kwargs, more):
    obj = kind.factory(**kwargs)

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert "Atnaujinti ir uždaryti</button>" in actual
    assert url in actual
    assert f'<h5 class="modal-title">{kind.modal_title}</h5>' in actual
    assert 'name="date" value="1999-01-01"' in actual
    assert 'name="price" value="0.01"' in actual
    assert (
        f'<option value="{obj.from_account.pk}" selected>{kind.from_title}</option>'
        in actual
    )
    assert (
        f'<option value="{obj.to_account.pk}" selected>{kind.to_title}</option>'
        in actual
    )
    for snippet in more:
        assert snippet.format(to=obj.to_account.pk) in actual


@pytest.mark.parametrize(
    "kind, extra",
    [
        pytest.param(KINDS["transactions"], {}, id="transactions"),
        pytest.param(KINDS["savings_close"], {"fee": "99"}, id="savings_close"),
        pytest.param(KINDS["savings_change"], {"fee": "99"}, id="savings_change"),
    ],
)
def test_update_to_another_year(client_logged, kind, extra):
    tr = kind.factory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "to_account": tr.to_account.pk,
        "from_account": tr.from_account.pk,
    } | extra
    url = reverse(kind.update_url, kwargs={"pk": tr.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert "2010-12-31" not in actual


@pytest.mark.parametrize(
    "kind, extra",
    [
        pytest.param(KINDS["transactions"], {"price": "150"}, id="transactions"),
        pytest.param(
            KINDS["savings_change"],
            {"price": "0.01", "fee": "0.01"},
            id="savings_change",
        ),
    ],
)
def test_update_switch_accounts(client_logged, kind, extra):
    obj = kind.factory()
    old_from, old_to = obj.from_account_id, obj.to_account_id

    data = {
        "date": "1999-12-31",
        "from_account": old_to,
        "to_account": old_from,
    } | extra
    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = kind.model.objects.get(pk=obj.pk)

    assert actual.from_account_id == old_to
    assert actual.to_account_id == old_from


def _foreign_move(kind, journal):
    return kind.factory(
        to_account=kind.to_factory(journal=journal, title="a1"),
        from_account=kind.from_factory(journal=journal, title="a2"),
        price=666,
    )


@by_kind
@pytest.mark.parametrize(
    "url_name_of",
    [
        pytest.param(lambda kind: kind.update_url, id="update"),
        pytest.param(lambda kind: kind.delete_url, id="delete"),
    ],
)
def test_other_journal_form_not_found(client_logged, second_user, kind, url_name_of):
    obj = _foreign_move(kind, second_user.journal)

    url = reverse(url_name_of(kind), kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@by_kind
def test_delete_load_form(client_logged, kind):
    p = kind.factory()

    url = reverse(kind.delete_url, kwargs={"pk": p.pk})
    response = client_logged.get(url)
    actual = response.content.decode("utf-8")

    assert url in actual
    assert '<form method="POST"' in actual
    assert f'hx-post="{url}"' in actual
    assert f"Ar tikrai norite ištrinti: <strong>{kind.delete_text}</strong>?" in actual


@by_kind
def test_delete(client_logged, kind):
    p = kind.factory()
    assert kind.model.objects.count() == 1

    url = reverse(kind.delete_url, kwargs={"pk": p.pk})
    client_logged.post(url, follow=True)

    assert kind.model.objects.count() == 0


@by_kind
def test_delete_other_journal_post_form(client_logged, second_user, kind):
    obj = _foreign_move(kind, second_user.journal)

    url = reverse(kind.delete_url, kwargs={"pk": obj.pk})
    client_logged.post(url, follow=True)

    assert kind.model.objects.count() == 1


def _post_update(client_logged, kind, follow=False, **extra):
    obj = kind.factory()
    data = {
        "price": "0.01",
        "date": "1999-12-31",
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
    } | extra

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    return client_logged.post(url, data, follow=follow)


def _assert_updated(actual, kind):
    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.to_account.title == kind.to_title
    assert actual.from_account.title == kind.from_title


@by_fee
def test_update(client_logged, kind, posted, fee):
    _post_update(client_logged, kind, **posted)
    actual = kind.model.objects.get()

    _assert_updated(actual, kind)
    assert model_to_dict(actual, fields=fee) == fee


@by_kind
def test_update_lands_on_its_list(client_logged, kind):
    response = _post_update(client_logged, kind, follow=True)
    page = response.content.decode("utf-8")

    row = (
        r'<td class="text-left[^"]*">1999-12-31</td>\s*'
        rf'<td class="text-left">{kind.from_title}</td>\s*'
        rf'<td class="text-left">{kind.to_title}</td>'
    )
    assert re.search(row, page)


def _new_url(kind):
    return reverse(kind.new_url)


def _closed_fund_update_url(kind, later_move=False):
    fund = SavingTypeFactory(closed=1999)
    obj = kind.factory(from_account=fund)
    if later_move:
        kind.factory(from_account=fund, date=date(1999, 6, 1))
    return reverse(kind.update_url, kwargs={"pk": obj.pk})


@by_fund_move
@pytest.mark.parametrize(
    "url_of, checked",
    [
        pytest.param(_new_url, 0, id="new"),
        pytest.param(_closed_fund_update_url, 1, id="update_of_a_closed_fund"),
        pytest.param(
            partial(_closed_fund_update_url, later_move=True),
            0,
            id="update_of_an_earlier_move",
        ),
    ],
)
@time_machine.travel("1999-1-1")
def test_close_checkbox_initial_value(client_logged, kind, url_of, checked):
    response = client_logged.get(url_of(kind))
    actual = response.content.decode("utf-8")

    assert len(CHECKED_BOX.findall(actual)) == checked


@by_fund_move
@pytest.mark.parametrize(
    "closed, close, expect",
    [
        pytest.param(1999, True, 1999, id="closed_stays_closed"),
        pytest.param(None, True, 1999, id="open_closes_in_the_moves_year"),
        pytest.param(1999, False, None, id="unticked_reopens"),
    ],
)
@time_machine.travel("2000-1-1")
def test_update_in_future_checkbox_value(client_logged, kind, closed, close, expect):
    a = SavingTypeFactory(closed=closed)
    obj = kind.factory(from_account=a)

    data = {
        "date": obj.date,
        "price": obj.price,
        "fee": obj.fee,
        "from_account": obj.from_account.pk,
        "to_account": obj.to_account.pk,
        "close": close,
    }

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # the fund closes in the move's year, not in the year it is edited
    assert actual.closed == expect


def _delete(client_logged, sell, other):
    client_logged.post(reverse("transactions:savings_close_delete", args=[sell.pk]))


def _move_to_another_fund(client_logged, sell, other):
    data = {
        "date": sell.date,
        "price": "15",
        "from_account": other.pk,
        "to_account": sell.to_account.pk,
    }
    url = reverse("transactions:savings_close_update", args=[sell.pk])
    client_logged.post(url, data)


# a partial sell before the closing one does not become the close
# the grid ends a year after the journal's last savings row; a moved sell keeps 2023
@pytest.mark.parametrize(
    "edit, years_after",
    [
        pytest.param(_delete, {2020, 2021, 2022, 2023}, id="delete"),
        pytest.param(
            _move_to_another_fund, {2020, 2021, 2022, 2023, 2024}, id="move_away"
        ),
    ],
)
@time_machine.travel("2024-1-1")
@pytest.mark.syncs
def test_closing_sell_removed_reopens_the_fund(
    client_logged, main_user, edit, years_after
):
    with quiet_build(main_user):
        bank = AccountFactory(title="Bank")
        fund = SavingTypeFactory(title="Fund")
        other = SavingTypeFactory(title="Other")
        SavingFactory(account=bank, saving_type=fund, date=date(2020, 1, 1), price=1000)
        SavingCloseFactory(
            from_account=fund, to_account=bank, date=date(2021, 1, 1), price=100
        )
        SavingFactory(account=bank, saving_type=fund, date=date(2022, 1, 1), price=500)
    data = {
        "date": "2023-01-01",
        "price": "15",
        "from_account": fund.pk,
        "to_account": bank.pk,
        "close": "on",
    }
    client_logged.post(reverse("transactions:savings_close_new"), data)
    sell = models.SavingClose.objects.get(date=date(2023, 1, 1))
    assert SavingType.objects.get(pk=fund.pk).closed == 2023

    edit(client_logged, sell, other)

    assert SavingType.objects.get(pk=fund.pk).closed is None
    years = SavingBalance.objects.filter(saving_type=fund).values_list("year")
    assert {year for (year,) in years} == years_after


def test_savings_change_not_show_other_journal_types(client_logged, second_user):
    a_from = SavingTypeFactory()
    SavingTypeFactory(title="Own")
    SavingTypeFactory(title="XXX", journal=second_user.journal)

    data = {
        "date": "1999-01-01",
        "from_account": a_from.pk,
    }
    url = reverse("transactions:savings_change_new")
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert actual.count(">Own</option>") == 2
    assert "XXX" not in actual


def test_load_saving_type_lists_the_open_funds_except_the_source(
    client_logged, second_user
):
    s1 = SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=1000)
    s3 = SavingTypeFactory(title="S3")
    SavingTypeFactory(title="S4", journal=second_user.journal)

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, {"from_account": s1.pk})
    actual = response.content.decode("utf-8")

    assert "S1" not in actual
    assert "S2" not in actual
    assert "S4" not in actual
    assert f'<option value="{s3.pk}">S3</option>' in actual


@pytest.mark.parametrize(
    "data",
    [
        pytest.param({}, id="no-value"),
        pytest.param({"from_account": ""}, id="empty"),
        pytest.param({"from_account": "x"}, id="not-a-number"),
        pytest.param({"from_account": "0"}, id="zero"),
    ],
)
def test_load_saving_type_empty_parent_pk(client_logged, data):
    SavingTypeFactory(title="S1")

    url = reverse("transactions:load_saving_type")
    response = client_logged.get(url, data)

    assert response.status_code == 200
    assert "S1" not in response.content.decode("utf-8")


def test_load_saving_type_must_logged(client):
    url = reverse("transactions:load_saving_type")

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.resolver_match.func.view_class is Login


@pytest.mark.parametrize(
    "view_class",
    [views.TabTransactions, views.TabSales, views.TabSwitches, views.TabAccounts],
    ids=["transactions", "sales", "switches", "accounts"],
)
def test_a_user_with_no_year_raises(rf, main_user, view_class):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        view_for(rf, main_user, view_class, scope="open").get_queryset()
