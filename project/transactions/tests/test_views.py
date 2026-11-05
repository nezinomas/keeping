import json
import re
from datetime import date
from functools import partial

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
from ...savings.services.model_services import SavingTypeModelService
from ...savings.tests.factories import SavingFactory, SavingTypeFactory
from .. import models, views
from ..tabs import TABS
from .factories import SavingChangeFactory, SavingCloseFactory, TransactionFactory
from .kinds import KINDS, by_fund_move, by_kind

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


CHECKED_BOX = re.compile(r'<input type="checkbox" .*? checked>')
OPTION = re.compile(r'<option value="(\d+)">([^<]*)</option>')
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
    "accounts": lambda i: (
        AccountFactory(title=f"F{i}"),
        AccountFactory(title=f"C{i}", closed=1998),
    ),
}


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_query_count_does_not_grow_with_the_rows(client_logged, tab):
    a_move_out_of = A_MOVE_OUT_OF[tab.name]

    def tab_queries():
        return count_queries(lambda: _tab(client_logged, tab.url))

    for i in range(2):
        a_move_out_of(i)
    two = tab_queries()

    for i in range(2, 6):
        a_move_out_of(i)
    six = tab_queries()

    assert six == two


def _tab(client, url):
    return client.get(url, headers={"HX-Request": "true"}).content.decode()


def _transactions(second_user):
    TransactionFactory(date=date(1999, 1, 5), from_account=AccountFactory(title="A"))
    TransactionFactory(
        date=date(1999, 3, 9), price=100_000_000, from_account=AccountFactory(title="B")
    )
    TransactionFactory(date=date(1999, 3, 2), from_account=AccountFactory(title="C"))
    _foreign_move(KINDS["transaction"], second_user.journal)


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
    _foreign_move(KINDS["sale"], second_user.journal)
    _foreign_move(KINDS["switch"], second_user.journal)


CLOSED = ' <span class="main__mark">Uždaryta</span>'
MOVE_ROW = (
    r'<tr [^>]*class="([^"]*)">\s*<td class="text-left main__date">([^<]*)</td>'
    r'\s*<td class="text-left main__name">(.*?)</td>'
    r'\s*<td class="text-left main__name">(.*?)</td>'
    r'\s*<td class="main__figure">([^<]*)</td>'
)
FUND_MOVE_ROW = MOVE_ROW + r'\s*<td class="main__figure main__fold">([^<]*)</td>'
FEES = [("price-col main__fold", "Mokesčiai")]


def _head(from_header, to_header, fees=()):
    return [
        ("text-left", "Data"),
        ("text-left main__name", from_header),
        ("text-left main__name", to_header),
        ("price-col", "Suma"),
        *fees,
        ("edit-col", ""),
        ("delete-col", ""),
    ]


@pytest.mark.parametrize(
    "scene, url_name, head, row, rows",
    [
        pytest.param(
            _transactions,
            "transactions:tab_transactions",
            _head("Iš sąskaitos", "Į sąskaitą"),
            MOVE_ROW,
            [
                ("", "1999-03-09", "B", "Account2", "1.000.000,00"),
                ("", "1999-03-02", "C", "Account2", "2,00"),
                ("table-group-divider", "1999-01-05", "A", "Account2", "2,00"),
            ],
            id="transactions",
        ),
        pytest.param(
            _fund_moves,
            "transactions:tab_sales",
            _head("Iš fondo", "Į sąskaitą", FEES),
            FUND_MOVE_ROW,
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
            _fund_moves,
            "transactions:tab_switches",
            _head("Iš fondo", "Į fondą", FEES),
            FUND_MOVE_ROW,
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
def test_a_move_tab_lists_the_years_moves_newest_first_marking_the_close(
    client_logged, second_user, scene, url_name, head, row, rows
):
    scene(second_user)

    content = _tab(client_logged, reverse(url_name))

    assert '<table class="main striped hover sticky-table">' in content
    assert re.findall(r'<th class="([^"]*)">([^<]*)</th>', content) == head
    assert re.findall(row, content) == rows


TAB_ACCOUNTS = "/transactions/accounts/"
CLOSED_BUTTON = re.compile(
    r'\s*<button type="button" class="filter-line__item" @click="shown = ! shown"'
    r""" :aria-current="shown \? 'true' : null">Uždarytos sąskaitos</button>\s*"""
)
TAB_PART = re.compile(
    r'<table class="main striped hover sticky-table"(?P<attrs>[^>]*)>'
    r"(?P<body>.*?)</table>"
    r'|<div class="alert">\s*(?P<notice>[^<]*?)\s*</div>'
    r'|(?P<scope><div x-data="\{ shown: false \}">\s*)?'
    r'<nav class="filter-line"(?P<nav_attrs>[^>]*)>(?P<nav>.*?)</nav>',
    re.DOTALL,
)
HEADER = [("text-left main__name", "Sąskaita"), ("edit-col", "")]
FOLDED = ' x-show="shown" x-cloak'
BUTTON = "the closed accounts' button"
OTHER_FILTER_LINE = "another filter line"


def _accounts_tab(content):
    """The tab's tables, notice and filter lines, in page order."""
    parts = []
    for part in TAB_PART.finditer(content):
        if part["notice"] is not None:
            parts.append(part["notice"])
        elif part["nav"] is not None:
            button = part["scope"] and not part["nav_attrs"]
            parts.append(
                BUTTON
                if button and CLOSED_BUTTON.fullmatch(part["nav"])
                else OTHER_FILTER_LINE
            )
        else:
            parts.append(
                (
                    part["attrs"],
                    re.findall(r'<th class="([^"]*)">([^<]*)</th>', part["body"]),
                    re.findall(
                        r'<tr hx-get="[^"]*" hx-trigger="dblclick"'
                        r' hx-target="#mainModal">\s*'
                        r'<td class="text-left main__name">(.*?)</td>',
                        part["body"],
                    ),
                )
            )
    return parts


@pytest.mark.parametrize(
    "year, parts",
    [
        pytest.param(
            2022,
            [
                ("", HEADER, ["Zeta", "Alpha", "Beta", "Edge"]),
                BUTTON,
                (
                    FOLDED,
                    HEADER,
                    [
                        '<s>Young</s> <span class="main__closed">uždaryta 2019</span>',
                        '<s>Ancient</s> <span class="main__closed">uždaryta 2021</span>',
                        '<s>Old</s> <span class="main__closed">uždaryta 2021</span>',
                    ],
                ),
            ],
            id="closed_before",
        ),
        pytest.param(
            2019,
            [
                (
                    "",
                    HEADER,
                    ["Old", "Young", "Zeta", "Alpha", "Beta", "Ancient", "Edge"],
                )
            ],
            id="none_closed_before",
        ),
    ],
)
def test_the_accounts_tab_lists_the_open_then_folds_the_closed(
    client_logged, main_user, second_user, year, parts
):
    main_user.year = year
    main_user.save()
    AccountFactory(title="Zeta", order=1)
    AccountFactory(title="Beta", order=2, closed=2024)
    AccountFactory(title="Alpha", order=2)
    AccountFactory(title="Edge", order=3, closed=2022)
    AccountFactory(title="Old", order=1, closed=2021)
    AccountFactory(title="Young", order=1, closed=2019)
    AccountFactory(title="Ancient", order=3, closed=2021)
    AccountFactory(title="Foreign", order=1, journal=second_user.journal)

    content = client_logged.get(TAB_ACCOUNTS).content.decode()

    assert _accounts_tab(content) == parts


def test_no_open_account_draws_the_notice_above_the_closed_ones(client_logged):
    AccountFactory(title="Old", closed=1998)

    content = _tab(client_logged, TAB_ACCOUNTS)

    assert _accounts_tab(content) == [
        "1999 metais įrašų nėra.",
        BUTTON,
        (
            FOLDED,
            HEADER,
            ['<s>Old</s> <span class="main__closed">uždaryta 1998</span>'],
        ),
    ]


# each row's tab, what builds it, and the forms its buttons open, in column order
ROW_FORMS = {
    **{
        name: (
            kind.tab_url,
            kind.factory,
            [("edit-col", kind.update_url), ("delete-col", kind.delete_url)],
        )
        for name, kind in KINDS.items()
    },
    "account": (
        "transactions:tab_accounts",
        AccountFactory,
        [("edit-col", "accounts:update")],
    ),
}
ROW = re.compile(
    r'<tr hx-get="([^"]*)" hx-trigger="dblclick" hx-target="#mainModal"[^>]*>'
    r"(.*?)</tr>",
    re.DOTALL,
)
ROW_BUTTON = re.compile(
    r'<td class="(edit-col|delete-col)">\s*<a role="button" hx-get="([^"]*)"'
)


@pytest.mark.parametrize(
    "tab_url, factory, forms", ROW_FORMS.values(), ids=ROW_FORMS.keys()
)
def test_a_row_opens_its_own_forms(client_logged, tab_url, factory, forms):
    record = factory()

    content = _tab(client_logged, reverse(tab_url))

    rows = [(url, ROW_BUTTON.findall(cells)) for url, cells in ROW.findall(content)]
    buttons = [(column, reverse(name, args=[record.pk])) for column, name in forms]
    _, update = buttons[0]  # a double click opens what the edit button opens
    assert rows == [(update, buttons)]


@by_kind
def test_a_tab_on_an_empty_year_draws_the_paper_notice(client_logged, kind):
    kind.factory(date=date(2000, 1, 1))

    content = _tab(client_logged, reverse(kind.tab_url))

    assert re.search(r'<div class="alert">\s*1999 metais įrašų nėra.\s*</div>', content)


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
        ("accounts", "/transactions/accounts/"),
    ]


def _post_data(a_from, a_to, **fields):
    return {
        "date": "1999-01-01",
        "price": "0.01",
        "from_account": a_from.pk,
        "to_account": a_to.pk,
    } | fields


def _move_form_data(move):
    return _post_data(move.from_account, move.to_account)


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

    assert '<input type="text" name="date" value="1999-01-01"' in actual


@by_kind
@pytest.mark.parametrize(
    "url_of",
    [
        pytest.param(lambda kind: reverse(kind.new_url), id="new"),
        pytest.param(
            lambda kind: reverse(kind.update_url, kwargs={"pk": kind.factory().pk}),
            id="update",
        ),
    ],
)
def test_a_form_posts_to_its_own_url_under_the_kinds_title(client_logged, kind, url_of):
    url = url_of(kind)

    actual = client_logged.get(url).content.decode("utf-8")

    assert re.search(rf'<form [^>]*hx-post="{url}"', actual)
    assert f'<h5 class="modal-title">{kind.modal_title}</h5>' in actual


def _post_new(client_logged, kind, **extra):
    a_from = kind.from_factory(title="From")
    a_to = kind.to_factory(title="To")
    client_logged.post(reverse(kind.new_url), _post_data(a_from, a_to, **extra))

    return kind.model.objects.get(), a_from, a_to


def _assert_saved(actual, a_from, a_to):
    assert actual.date == date(1999, 1, 1)
    assert actual.price == 1
    assert actual.from_account == a_from
    assert actual.to_account == a_to


# a Transaction has no Fee; a fund move's posted Fee is stored in cents
by_fee = pytest.mark.parametrize(
    "kind, posted, fee",
    [
        pytest.param(KINDS["transaction"], {}, {}, id="transaction"),
        pytest.param(KINDS["sale"], {"fee": "0.01"}, {"fee": 1}, id="sale"),
        pytest.param(KINDS["switch"], {"fee": "0.01"}, {"fee": 1}, id="switch"),
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
    assert re.findall(
        r'<(?:input|select) [^>]*name="(\w+)"[^>]*aria-invalid="true"', actual
    ) == ["date", "from_account", "to_account", "price"]


@pytest.mark.parametrize(
    "kind, kwargs, more",
    [
        pytest.param(
            KINDS["transaction"],
            {"price": 1},
            ('<option value="{to}">Account2</option>',),
            id="transaction",
        ),
        pytest.param(
            KINDS["sale"],
            {"price": 1, "fee": 1},
            ('name="fee" value="0.01"',),
            id="sale",
        ),
        pytest.param(
            KINDS["switch"],
            {"price": 1, "fee": 1},
            ('name="fee" value="0.01"', '<option value="{to}">Savings To</option>'),
            id="switch",
        ),
    ],
)
def test_load_update_form(client_logged, kind, kwargs, more):
    obj = kind.factory(**kwargs)

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    actual = clean_content(response.content.decode("utf-8"))

    assert "Atnaujinti ir uždaryti</button>" in actual
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
        pytest.param(KINDS["transaction"], {}, id="transaction"),
        pytest.param(KINDS["sale"], {"fee": "99"}, id="sale"),
        pytest.param(KINDS["switch"], {"fee": "99"}, id="switch"),
    ],
)
def test_update_to_another_year(client_logged, kind, extra):
    tr = kind.factory()

    data = _post_data(
        tr.from_account, tr.to_account, price="150", date="2010-12-31", **extra
    )
    url = reverse(kind.update_url, kwargs={"pk": tr.pk})
    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert re.findall(r'<td class="text-left main__date">([^<]*)</td>', actual) == []


@pytest.mark.parametrize(
    "kind, extra",
    [
        pytest.param(KINDS["transaction"], {"price": "150"}, id="transaction"),
        pytest.param(
            KINDS["switch"],
            {"price": "0.01", "fee": "0.01"},
            id="switch",
        ),
    ],
)
def test_update_switch_accounts(client_logged, kind, extra):
    obj = kind.factory()
    old_from, old_to = obj.from_account_id, obj.to_account_id

    data = _post_data(obj.to_account, obj.from_account, date="1999-12-31", **extra)
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

    assert re.search(rf'<form method="POST"[^>]*hx-post="{url}"', actual)
    assert '<h5 class="modal-title">Trint pervedimą</h5>' in actual
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
    data = _post_data(obj.from_account, obj.to_account, date="1999-12-31", **extra)

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
        r'<td class="text-left main__date">1999-12-31</td>\s*'
        rf'<td class="text-left main__name">{kind.from_title}</td>\s*'
        rf'<td class="text-left main__name">{kind.to_title}</td>'
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

    data = _post_data(
        obj.from_account,
        obj.to_account,
        date=obj.date,
        price=obj.price,
        fee=obj.fee,
        close=close,
    )

    url = reverse(kind.update_url, kwargs={"pk": obj.pk})
    client_logged.post(url, data)
    actual = SavingType.objects.get(pk=a.pk)

    # the fund closes in the move's year, not in the year it is edited
    assert actual.closed == expect


def _delete(client_logged, sell):
    client_logged.post(reverse("transactions:savings_close_delete", args=[sell.pk]))


def _move_to_another_fund(client_logged, sell, other):
    data = _post_data(other, sell.to_account, date=sell.date, price="15")
    url = reverse("transactions:savings_close_update", args=[sell.pk])
    client_logged.post(url, data)


# the grid ends a year after the journal's last savings row; a moved sell keeps 2023
@pytest.mark.parametrize(
    "edit, years_after",
    [
        pytest.param(
            lambda client, sell, other: _delete(client, sell),
            {2020, 2021, 2022, 2023},
            id="delete",
        ),
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
    data = _post_data(fund, bank, date="2023-01-01", price="15", close="on")
    client_logged.post(reverse("transactions:savings_close_new"), data)
    sell = models.SavingClose.objects.get(date=date(2023, 1, 1))
    assert SavingType.objects.get(pk=fund.pk).closed == 2023

    edit(client_logged, sell, other)

    assert fund in SavingTypeModelService(main_user).items(year=2024)
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

    to_account = re.search(r'<select name="to_account".*?</select>', actual, re.DOTALL)
    assert [title for _, title in OPTION.findall(to_account[0])] == ["Own"]


@pytest.mark.parametrize(
    "view_class",
    [views.TabTransactions, views.TabSales, views.TabSwitches, views.TabAccounts],
    ids=["transactions", "sales", "switches", "accounts"],
)
def test_a_user_with_no_year_raises(rf, main_user, view_class):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        view_for(rf, main_user, view_class).get_queryset()
