import json
import re
from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ...accounts.tests.factories import AccountFactory
from ...core.tests.utils import (
    FOLD_BUTTON,
    FOLDED,
    HEAD_CELL,
    PAPER_PARTS,
    clean_content,
    closed_fold,
    count_queries,
    form_posts_to,
    paper_page_parts,
    quick_add_pills,
    row_forms,
    tab_fragment,
    view_for,
)
from ...pensions.tests.factories import PensionFactory, PensionTypeFactory
from .. import models, views
from ..services.model_services import SavingTypeModelService
from ..tabs import TABS
from .factories import Saving, SavingFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db


TAB_TITLES = {
    "savings": "Taupymas",
    "funds": "Fondai",
    "pensions": "II pakopa",
    "pension_funds": "II pakopos fondai",
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

    assert f"<title>Taupymas | {TAB_TITLES[tab.name]}</title>" in content
    assert paper_page_parts(content) == dict.fromkeys(PAPER_PARTS, whole)


# each row in a Fund and from an Account of its own, so a read per owner grows
A_ROW_OF_ITS_OWN = {
    "savings": lambda i: SavingFactory(
        saving_type=SavingTypeFactory(title=f"F{i}"),
        account=AccountFactory(title=f"A{i}"),
    ),
    "funds": lambda i: (
        SavingTypeFactory(title=f"Open{i}"),
        SavingTypeFactory(title=f"Closed{i}", closed=1990),
    ),
    "pensions": lambda i: PensionFactory(
        pension_type=PensionTypeFactory(title=f"P{i}")
    ),
    "pension_funds": lambda i: PensionTypeFactory(title=f"P{i}"),
}


@pytest.mark.parametrize("tab", TABS, ids=lambda tab: tab.name)
def test_tab_query_count_does_not_grow_with_the_rows(client_logged, tab):
    a_row_of_its_own = A_ROW_OF_ITS_OWN[tab.name]

    def tab_queries():
        return count_queries(lambda: tab_fragment(client_logged, tab.url))

    for i in range(2):
        a_row_of_its_own(i)
    two = tab_queries()

    for i in range(2, 6):
        a_row_of_its_own(i)
    six = tab_queries()

    assert six == two


SAVING_ROW = re.compile(
    r'<tr [^>]*class="([^"]*)">\s*<td class="text-left main__date">([^<]*)</td>'
    r'\s*<td class="text-left main__name">([^<]*)</td>'
    r'\s*<td class="text-left main__fold">([^<]*)</td>'
    r'\s*<td class="text-left main__fold">([^<]*)</td>'
    r'\s*<td class="main__figure" data-cell="[^"]*">([^<]*)</td>'
    r'\s*<td class="main__figure main__fold" data-cell="[^"]*">([^<]*)</td>'
)


TAB_PENSIONS = "/savings/pensions/"
PENSION_ROW = re.compile(
    r'<tr [^>]*class="([^"]*)">\s*<td class="text-left main__date">([^<]*)</td>'
    r'\s*<td class="text-left main__name">([^<]*)</td>'
    r'\s*<td class="text-left main__fold">([^<]*)</td>'
    r'\s*<td class="main__figure" data-cell="[^"]*">([^<]*)</td>'
    r'\s*<td class="main__figure main__fold" data-cell="[^"]*">([^<]*)</td>'
)


# each tab of Savings or Pensions, what builds one of its rows, and the row it draws
DATED_TABS = {
    "savings": ("/savings/", SavingFactory, SAVING_ROW),
    "pensions": (TAB_PENSIONS, PensionFactory, PENSION_ROW),
}
DIVIDER = "table-group-divider"


def _saving(on, name, price, **owner):
    SavingFactory(
        date=date.fromisoformat(on),
        saving_type=SavingTypeFactory(title=f"Fund {name}", **owner),
        account=AccountFactory(title=f"Account {name}", **owner),
        remark=f"remark {name}",
        price=price,
        fee=price // 10,
    )


def _pension(on, name, price, **owner):
    PensionFactory(
        date=date.fromisoformat(on),
        pension_type=PensionTypeFactory(title=f"Fund {name}", **owner),
        remark=f"remark {name}",
        price=price,
        fee=price // 10,
    )


@pytest.mark.parametrize(
    "tab, build, head, rows",
    [
        pytest.param(
            "savings",
            _saving,
            [
                ("text-left", "Data"),
                ("text-left main__name", "Fondas"),
                ("text-left main__fold", "Iš sąskaitos"),
                ("text-left main__fold", "Pastaba"),
                ("price-col", "Suma"),
                ("price-col main__fold", "Mokesčiai"),
                ("edit-col", ""),
                ("delete-col", ""),
            ],
            [
                ("", "1999-03-09", "Fund A", "Account A", "remark A", "1,00", "0,10"),
                ("", "1999-03-02", "Fund B", "Account B", "remark B", "2,00", "0,20"),
                (
                    DIVIDER,
                    "1999-01-05",
                    "Fund C",
                    "Account C",
                    "remark C",
                    "3,00",
                    "0,30",
                ),
            ],
            id="savings",
        ),
        pytest.param(
            "pensions",
            _pension,
            [
                ("text-left", "Data"),
                ("text-left main__name", "Fondas"),
                ("text-left main__fold", "Pastaba"),
                ("price-col", "Suma"),
                ("price-col main__fold", "Mokesčiai"),
                ("edit-col", ""),
                ("delete-col", ""),
            ],
            [
                ("", "1999-03-09", "Fund A", "remark A", "1,00", "0,10"),
                ("", "1999-03-02", "Fund B", "remark B", "2,00", "0,20"),
                (DIVIDER, "1999-01-05", "Fund C", "remark C", "3,00", "0,30"),
            ],
            id="pensions",
        ),
    ],
)
def test_a_dated_tab_lists_the_years_rows_newest_first(
    client_logged, second_user, tab, build, head, rows
):
    build("1999-01-05", "C", 300)
    build("1999-03-09", "A", 100)
    build("1999-03-02", "B", 200)
    build("2000-01-01", "D", 400)
    build("1999-02-01", "E", 500, journal=second_user.journal)
    tab_url, _, row = DATED_TABS[tab]

    content = tab_fragment(client_logged, tab_url)

    assert HEAD_CELL.findall(content) == head
    assert row.findall(content) == rows


@time_machine.travel("2000-01-01")
def test_saving_load_new_form(client_logged):
    url = reverse("savings:new")

    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert "1999-01-01" in actual
    assert url in actual


@time_machine.travel("1999-1-1")
def test_saving_save(client_logged):
    a = AccountFactory()
    i = SavingTypeFactory()

    data = {
        "date": "1999-01-01",
        "price": "0.01",
        "fee": "2",
        "account": a.pk,
        "saving_type": i.pk,
    }

    url = reverse("savings:new")

    response = client_logged.post(url, data, follow=True)

    actual = response.content.decode("utf-8")

    assert SAVING_ROW.findall(actual) == [
        ("", "1999-01-01", "Savings", "Account1", "", "0,01", "2,00")
    ]


def test_saving_save_invalid_data(client_logged):
    data = {"date": "x", "price": "x", "fee": "x", "account": "x", "saving_type": "x"}

    url = reverse("savings:new")

    response = client_logged.post(url, data)

    actual = response.context["form"]

    assert not actual.is_valid()
    assert "date" in actual.errors
    assert "price" in actual.errors
    assert "fee" in actual.errors
    assert "account" in actual.errors
    assert "saving_type" in actual.errors


def test_savings_load_update_form(client_logged):
    obj = SavingFactory()

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.content.decode("utf-8")

    assert url in form
    assert "Atnaujinti ir uždaryti</button>" in clean_content(form)


def test_savings_load_update_form_field_values(client_logged):
    obj = SavingFactory(price=1, fee=1)

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert form.instance.fee == 0.01
    assert form.instance.account.title == "Account1"
    assert form.instance.saving_type.title == "Savings"
    assert form.instance.remark == "remark"


def test_savings_load_update_form_field_values_fee_none(client_logged):
    obj = SavingFactory(price=1, fee=0)

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)
    form = response.context["form"]

    assert form.instance.date == date(1999, 1, 1)
    assert form.instance.price == 0.01
    assert not form.instance.fee
    assert form.instance.account.title == "Account1"
    assert form.instance.saving_type.title == "Savings"
    assert form.instance.remark == "remark"


@pytest.mark.parametrize(
    "field, price, fee", [("price", 0, 1), ("fee", 1, 0)], ids=["price", "fee"]
)
def test_savings_update_form_shows_a_stored_zero_as_empty(
    client_logged, field, price, fee
):
    obj = SavingFactory(price=price, fee=fee)

    url = reverse("savings:update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    assert response.context["form"][field].value() == ""


@pytest.mark.parametrize("field", ["price", "fee"])
def test_savings_new_form_shows_an_empty_field_not_zero(client_logged, field):
    response = client_logged.get(reverse("savings:new"))

    assert response.context["form"][field].value() == ""


@time_machine.travel("2011-1-1")
def test_saving_update_to_another_year(client_logged):
    saving = SavingFactory()

    data = {
        "price": "150",
        "date": "2010-12-31",
        "remark": "Pastaba",
        "fee": "25",
        "account": saving.account.pk,
        "saving_type": saving.saving_type.pk,
    }
    url = reverse("savings:update", kwargs={"pk": saving.pk})

    response = client_logged.post(url, data, follow=True)
    actual = response.content.decode("utf-8")

    assert not SAVING_ROW.findall(actual)
    assert re.search(r'<div class="alert">\s*1999 metais įrašų nėra.\s*</div>', actual)


@time_machine.travel("1999-12-31")
@pytest.mark.parametrize(
    "fee, expect", [("0.01", 1), ("4.89", 489)], ids=["fee_001", "fee_489"]
)
def test_saving_update(client_logged, fee, expect):
    saving = SavingFactory()

    data = {
        "price": "0.01",
        "fee": fee,
        "date": "1999-12-31",
        "remark": "Pastaba",
        "account": saving.account.pk,
        "saving_type": saving.saving_type.pk,
    }
    url = reverse("savings:update", kwargs={"pk": saving.pk})

    client_logged.post(url, data, follow=True)
    actual = Saving.objects.get(pk=saving.pk)

    assert actual.date == date(1999, 12, 31)
    assert actual.price == 1
    assert actual.fee == expect
    assert actual.remark == "Pastaba"


def test_savings_not_load_other_journal(client_logged, second_user):
    a1 = AccountFactory(title="a1")
    a2 = AccountFactory(journal=second_user.journal, title="a2")

    it1 = SavingTypeFactory(title="xxx")
    it2 = SavingTypeFactory(title="yyy", journal=second_user.journal)

    SavingFactory(saving_type=it1, account=a1)
    i2 = SavingFactory(saving_type=it2, account=a2, price=666)

    url = reverse("savings:update", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "price, fee, shown_price, shown_fee",
    [
        pytest.param(7777, 8888, "77,77", "88,88", id="cents"),
        pytest.param(100_000_000, 100_000, "1.000.000,00", "1.000,00", id="thousands"),
    ],
)
@pytest.mark.parametrize("tab_url, factory, row", DATED_TABS.values(), ids=DATED_TABS)
@time_machine.travel("1999-1-1")
def test_a_dated_tab_shows_prices_converted(
    client_logged, tab_url, factory, row, price, fee, shown_price, shown_fee
):
    factory(price=price, fee=fee)

    (cells,) = row.findall(tab_fragment(client_logged, tab_url))

    assert cells[-2:] == (shown_price, shown_fee)


@pytest.mark.parametrize(
    "tab_url, factory", [tab[:2] for tab in DATED_TABS.values()], ids=DATED_TABS
)
@pytest.mark.parametrize(
    "rows, shown",
    [pytest.param(0, True, id="empty"), pytest.param(1, False, id="listed")],
)
def test_a_dated_tab_names_its_empty_year(client_logged, tab_url, factory, rows, shown):
    for _ in range(rows):
        factory()

    actual = tab_fragment(client_logged, tab_url)

    notice = r'<div class="alert">\s*1999 metais įrašų nėra\.\s*</div>'
    assert bool(re.search(notice, actual)) == shown


def test_view_saving_delete_load_form(client_logged):
    p = SavingFactory()

    url = reverse("savings:delete", kwargs={"pk": p.pk})
    response = client_logged.get(url)

    form = response.content.decode("utf-8")

    assert url in form
    assert '<form method="POST"' in form
    assert f'hx-post="{url}"' in form
    assert "Ar tikrai norite ištrinti: <strong>1999-01-01: Savings</strong>?" in form


def test_view_saving_delete(client_logged):
    p = SavingFactory()

    assert models.Saving.objects.all().count() == 1
    url = reverse("savings:delete", kwargs={"pk": p.pk})

    client_logged.post(url, follow=True)

    assert models.Saving.objects.all().count() == 0


def test_savings_delete_other_journal_get_form(client_logged, second_user):
    it2 = SavingTypeFactory(title="yyy", journal=second_user.journal)
    i2 = SavingFactory(
        saving_type=it2,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("savings:delete", kwargs={"pk": i2.pk})
    response = client_logged.get(url)

    assert response.status_code == 404


def test_savings_delete_other_journal_post_form(client_logged, second_user):
    it2 = SavingTypeFactory(title="yyy", journal=second_user.journal)
    i2 = SavingFactory(
        saving_type=it2,
        account=AccountFactory(title="A2", journal=second_user.journal),
        price=666,
    )

    url = reverse("savings:delete", kwargs={"pk": i2.pk})
    client_logged.post(url, follow=True)

    assert Saving.objects.all().count() == 1


def test_type_save_invalid_data(client_logged):
    data = {"title": ""}

    url = reverse("savings:type_new")

    response = client_logged.post(url, data, follow=True)

    actual = response.context["form"]

    assert not actual.is_valid()


TAB_FUNDS = "/savings/funds/"
FUND_HEADER = [("text-left main__name", "Fondas"), ("edit-col", "")]


def _funds_tab(content):
    return closed_fold(content, "Uždaryti fondai")


def _struck(title, year):
    return f'<s>{title}</s> <span class="main__closed">uždaryta {year}</span>'


@pytest.mark.parametrize(
    "year, parts",
    [
        pytest.param(
            2022,
            [
                (
                    "",
                    FUND_HEADER,
                    ["Delta", "Zeta", "Beta", "Alpha", "Edge", "Mid", "Late"],
                ),
                FOLD_BUTTON,
                (
                    FOLDED,
                    FUND_HEADER,
                    [
                        _struck("Young", 2019),
                        _struck("Old", 2021),
                        _struck("Ancient", 2021),
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
                    FUND_HEADER,
                    [
                        *["Delta", "Zeta", "Beta", "Alpha", "Young", "Old"],
                        "Ancient",
                        *["Edge", "Mid", "Late"],
                    ],
                )
            ],
            id="none_closed_before",
        ),
    ],
)
def test_the_funds_tab_lists_the_open_then_folds_the_closed(
    client_logged, main_user, second_user, year, parts
):
    main_user.year = year
    main_user.save()
    SavingTypeFactory(title="Alpha", type="shares")
    SavingTypeFactory(title="Zeta", type="funds")
    SavingTypeFactory(title="Delta", type="funds")
    SavingTypeFactory(title="Beta", type="pensions")
    SavingTypeFactory(title="Late", type="funds", closed=2025)
    SavingTypeFactory(title="Mid", type="shares", closed=2024)
    SavingTypeFactory(title="Edge", type="pensions", closed=2022)
    SavingTypeFactory(title="Ancient", type="shares", closed=2021)
    SavingTypeFactory(title="Old", type="pensions", closed=2021)
    SavingTypeFactory(title="Young", type="funds", closed=2019)
    SavingTypeFactory(title="Foreign", journal=second_user.journal)

    content = client_logged.get(TAB_FUNDS).content.decode()

    assert _funds_tab(content) == parts


# the update renames a fund of its own, so either save leaves one fund but YYY
FUND_SAVES = [
    pytest.param(lambda: reverse("savings:type_new"), id="new"),
    pytest.param(
        lambda: reverse(
            "savings:type_update", kwargs={"pk": SavingTypeFactory(title="XXX").pk}
        ),
        id="update",
    ),
]


@pytest.mark.parametrize("url_of", FUND_SAVES)
def test_a_fund_form_loads(client_logged, url_of):
    url = url_of()

    actual = client_logged.get(url).content.decode()

    assert form_posts_to(actual, "generic-form", url)


@pytest.mark.parametrize("url_of", FUND_SAVES)
@pytest.mark.parametrize(
    "closed, stored, parts",
    [
        pytest.param(
            "",
            None,
            [
                ("", FUND_HEADER, ["TTT"]),
                FOLD_BUTTON,
                (FOLDED, FUND_HEADER, [_struck("YYY", 1111)]),
            ],
            id="open",
        ),
        pytest.param(
            "1998",
            1998,
            [
                "1999 metais įrašų nėra.",
                FOLD_BUTTON,
                (FOLDED, FUND_HEADER, [_struck("YYY", 1111), _struck("TTT", 1998)]),
            ],
            id="closed_before_the_year",
        ),
    ],
)
def test_a_fund_save_lands_on_the_funds_tab_drawing_it(
    client_logged, url_of, closed, stored, parts
):
    SavingTypeFactory(title="YYY", closed=1111)
    data = {"title": "TTT", "type": "pensions", "fee_source": "account"}

    response = client_logged.post(url_of(), data | {"closed": closed}, follow=True)

    assert response.redirect_chain == [(TAB_FUNDS, 302)]
    assert models.SavingType.objects.exclude(title="YYY").values_list(
        "title", "type", "fee_source", "closed"
    ).get() == ("TTT", "pensions", "account", stored)
    assert _funds_tab(response.content.decode()) == parts


TAB_PENSION_FUNDS = "/savings/pension-funds/"


@pytest.mark.parametrize(
    "titles, parts",
    [
        pytest.param(
            ["Beta", "Alpha"], [("", FUND_HEADER, ["Alpha", "Beta"])], id="listed"
        ),
        pytest.param([], ["1999 metais įrašų nėra."], id="none"),
    ],
)
def test_the_pension_funds_tab_lists_every_fund_by_title(
    client_logged, second_user, titles, parts
):
    for title in titles:
        PensionTypeFactory(title=title)
    PensionTypeFactory(title="Foreign", journal=second_user.journal)

    content = client_logged.get(TAB_PENSION_FUNDS).content.decode()

    assert _funds_tab(content) == parts


def test_saving_type_not_load_other_journal(client_logged, second_user):
    SavingTypeFactory(title="xxx")
    obj = SavingTypeFactory(title="yyy", journal=second_user.journal)

    url = reverse("savings:type_update", kwargs={"pk": obj.pk})
    response = client_logged.get(url)

    actual = response.content.decode("utf-8")

    assert obj.title not in actual


def test_type_new_and_update_with_the_receiver_connected(client_logged):
    account = AccountFactory(title="IB")
    data = {"title": "VALL", "type": "funds", "fee_source": "investment"}

    response = client_logged.post(reverse("savings:type_new"), data, follow=True)
    assert response.status_code == 200
    saving_type = models.SavingType.objects.get(title="VALL")
    SavingFactory(account=account, saving_type=saving_type, price=200, fee=3)

    url = reverse("savings:type_update", kwargs={"pk": saving_type.pk})
    response = client_logged.post(url, data | {"fee_source": "account"}, follow=True)

    assert response.status_code == 200
    assert account.accounts_balance.get(year=1999).expenses == 203


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabSavings).get_queryset(),
            id="tab",
        ),
        pytest.param(lambda rf, u: SavingTypeModelService(u).items(), id="types"),
        pytest.param(
            lambda rf, u: view_for(rf, u, views.TabPensions).get_queryset(),
            id="pension_tab",
        ),
    ],
)
def test_a_user_with_no_year_raises(rf, main_user, call):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        call(rf, main_user)


# each row's tab, what builds it, and the forms its buttons open, in column order
ROW_FORMS = {
    "saving": (
        "savings:index",
        SavingFactory,
        [("edit-col", "savings:update"), ("delete-col", "savings:delete")],
    ),
    "fund": (
        "savings:tab_funds",
        SavingTypeFactory,
        [("edit-col", "savings:type_update")],
    ),
    "closed_fund": (
        "savings:tab_funds",
        lambda: SavingTypeFactory(closed=1998),
        [("edit-col", "savings:type_update")],
    ),
    "pension": (
        "savings:tab_pensions",
        PensionFactory,
        [("edit-col", "pensions:update"), ("delete-col", "pensions:delete")],
    ),
    "pension_fund": (
        "savings:tab_pension_funds",
        PensionTypeFactory,
        [("edit-col", "pensions:type_update")],
    ),
}


@pytest.mark.parametrize(
    "tab_url, factory, forms", ROW_FORMS.values(), ids=ROW_FORMS.keys()
)
def test_a_row_opens_its_own_forms(client_logged, tab_url, factory, forms):
    record = factory()

    content = tab_fragment(client_logged, reverse(tab_url))

    urls = [(col, reverse(name, kwargs={"pk": record.pk})) for col, name in forms]
    assert row_forms(content) == [(urls[0][1], urls)]


def test_quick_add_offers_its_pill(client_logged):
    content = client_logged.get(reverse("savings:index")).content.decode()

    assert quick_add_pills(content) == [
        ("button", "savings", 'hx-get="/savings/new/"', "Pridėti taupymą"),
        ("button", "funds", 'hx-get="/savings/type/new/"', "Pridėti fondą"),
        ("button", "pensions", 'hx-get="/pensions/new/"', "Pridėti įmoką"),
        (
            "button",
            "pension_funds",
            'hx-get="/pensions/type/new/"',
            "Pridėti II pakopos fondą",
        ),
    ]


def _saving_data(saving):
    return {
        "date": "1999-01-01",
        "price": "1",
        "fee": "0",
        "account": saving.account.pk,
        "saving_type": saving.saving_type.pk,
    }


SAVES = [
    pytest.param(lambda saving: reverse("savings:new"), _saving_data, id="new"),
    pytest.param(
        lambda saving: reverse("savings:update", kwargs={"pk": saving.pk}),
        _saving_data,
        id="update",
    ),
]
DELETE = pytest.param(
    lambda saving: reverse("savings:delete", kwargs={"pk": saving.pk}),
    lambda saving: {},
    id="delete",
)


def _fund_data(saving):
    return {"title": "TTT", "type": "funds", "fee_source": "investment"}


FUND_FORMS = [
    pytest.param(lambda saving: reverse("savings:type_new"), _fund_data, id="fund_new"),
    pytest.param(
        lambda saving: reverse(
            "savings:type_update", kwargs={"pk": saving.saving_type.pk}
        ),
        _fund_data,
        id="fund_update",
    ),
]


def _pension_data(saving):
    return {"date": "1999-01-01", "price": "1", "pension_type": PensionTypeFactory().pk}


def _pension_fund_data(saving):
    return {"title": "TTT"}


PENSION_SAVES = [
    pytest.param(
        lambda saving: reverse("pensions:new"), _pension_data, id="pension_new"
    ),
    pytest.param(
        lambda saving: reverse("pensions:update", kwargs={"pk": PensionFactory().pk}),
        _pension_data,
        id="pension_update",
    ),
]
PENSION_FORMS = [
    *PENSION_SAVES,
    pytest.param(
        lambda saving: reverse("pensions:delete", kwargs={"pk": PensionFactory().pk}),
        lambda saving: {},
        id="pension_delete",
    ),
    pytest.param(
        lambda saving: reverse("pensions:type_new"),
        _pension_fund_data,
        id="pension_fund_new",
    ),
    pytest.param(
        lambda saving: reverse(
            "pensions:type_update", kwargs={"pk": PensionTypeFactory().pk}
        ),
        _pension_fund_data,
        id="pension_fund_update",
    ),
]


@pytest.mark.parametrize(
    "url_of, data_of", [*SAVES, DELETE, *FUND_FORMS, *PENSION_FORMS]
)
def test_a_form_on_the_page_fires_reload(client_logged, url_of, data_of):
    saving = SavingFactory()

    response = client_logged.post(
        url_of(saving), data_of(saving), headers={"HX-Request": "true"}
    )

    assert json.loads(response.headers.get("HX-Trigger", "null")) == {"reload": {}}


def _landing(saves, tab_url):
    return [pytest.param(*save.values, tab_url, id=save.id) for save in saves]


# a delete answers 204 either way
@pytest.mark.parametrize(
    "url_of, data_of, tab_url",
    [*_landing(SAVES, "/savings/"), *_landing(PENSION_SAVES, TAB_PENSIONS)],
)
def test_a_saving_or_pension_save_without_htmx_lands_on_its_tab(
    client_logged, url_of, data_of, tab_url
):
    saving = SavingFactory()

    response = client_logged.post(url_of(saving), data_of(saving))

    assert response.url == tab_url
