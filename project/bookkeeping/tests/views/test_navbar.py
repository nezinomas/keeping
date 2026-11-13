import re

import pytest
from django.urls import reverse

from ....counts.tests.factories import CountTypeFactory

pytestmark = pytest.mark.django_db


def _active_links(client, path: str) -> list[str]:
    content = client.get(path).content.decode()

    return re.findall(r'<div class="active">\s*<a href="([^"]+)"', content)


def _nav(client, path: str) -> str:
    content = client.get(path).content.decode()

    return re.search(r'<nav id="main-nav">.*?</nav>', content, re.S).group()


@pytest.mark.parametrize(
    "path, url_name",
    [
        ("/", "bookkeeping:index"),
        ("/month/", "bookkeeping:month"),
        ("/detailed/", "bookkeeping:detailed"),
        ("/expenses/", "expenses:index"),
        ("/incomes/", "incomes:index"),
        ("/transactions/", "transactions:index"),
        ("/transactions/sales/", "transactions:index"),
        ("/savings/", "savings:index"),
        ("/savings/pension-funds/", "savings:index"),
        ("/debts/", "debts:index"),
        ("/books/", "books:index"),
        ("/drinks/", "drinks:index"),
        ("/counts/c/count-type/", "counts:redirect"),
        ("/plans/", "plans:index"),
        ("/summary/", "bookkeeping:summary"),
    ],
)
def test_the_navbar_marks_each_section_on_its_page(client_logged, path, url_name):
    CountTypeFactory()

    assert _active_links(client_logged, path) == [reverse(url_name)]


def test_the_navbar_marks_the_user_menu_on_settings(client_logged, main_user):
    main_user.is_superuser = True
    main_user.save()

    content = client_logged.get("/settings/").content.decode()

    assert re.search(
        rf'<div class="active">\s*<span>\s*{main_user.username}\s*</span>', content
    )


def test_the_navbar_menus_carry_no_flag(client_logged):
    nav = _nav(client_logged, "/")

    assert set(re.findall(r'<div class="(dropdown(?: [^"]*)?)"', nav)) == {"dropdown"}


@pytest.mark.parametrize(
    "item_url, tabs",
    [
        (
            "/transactions/",
            [
                ("transactions:tab_transactions", "Pervedimai"),
                ("transactions:tab_sales", "Fondų pardavimai"),
                ("transactions:tab_switches", "Fondų keitimai"),
                ("transactions:tab_accounts", "Sąskaitos"),
            ],
        ),
        (
            "/savings/",
            [
                ("savings:tab_savings", "Taupymas"),
                ("savings:tab_funds", "Fondai"),
                ("savings:tab_pensions", "II pakopa"),
                ("savings:tab_pension_funds", "II pakopos fondai"),
            ],
        ),
        (
            "/debts/",
            [
                ("debts:tab_lend", "Paskolinta"),
                ("debts:tab_lend_returns", "Grąžino"),
                ("debts:tab_borrow", "Pasiskolinta"),
                ("debts:tab_borrow_returns", "Grąžinau"),
            ],
        ),
    ],
)
def test_the_tab_menus_name_their_tabs_in_order(client_logged, item_url, tabs):
    nav = _nav(client_logged, "/")
    menus = re.findall(
        rf'<a href="{item_url}">[^<]*</a>\s*<div class="dropdown">'
        r'\s*<button class="dropdown__btn"></button>'
        r'\s*<div class="dropdown__menu">(.*?)</div>',
        nav,
        re.S,
    )

    assert [re.findall(r'<a href="([^"]+)">([^<]+)</a>', menu) for menu in menus] == [
        [(reverse(url_name), label) for url_name, label in tabs]
    ]


def test_the_navbar_names_the_selected_year(client_logged, main_user):
    main_user.year = 2004
    main_user.save()

    nav = _nav(client_logged, "/month/")

    assert re.search(r'<a href="/">\s*([^<]+?)\s*</a>', nav).group(1) == "2004"


def test_the_navbar_menus_without_a_page_stay_unlinked_where_a_page_has_a_url(
    client_logged, main_user
):
    # Books' Duomenys passes its own `url` to the page's context
    nav = _nav(client_logged, reverse("books:tab_data", args=["all"]))

    assert re.findall(r"<div>\s*<span>\s*([^<]+?)\s*</span>", nav) == [
        "Pridėti",
        main_user.username,
    ]


def test_the_navbar_acts_are_buttons_that_open_their_form(client_logged):
    nav = _nav(client_logged, "/")
    forms = [
        "/counts/type/new/",
        "/incomes/new/",
        "/expenses/new/",
        "/transactions/new/",
        "/savings/new/",
        "/accounts/new/",
        "/incomes/type/new/",
        "/expenses/type/new/",
        "/expenses/name/new/",
        "/savings/type/new/",
    ]

    assert re.findall(r'hx-get="([^"]+)"', nav) == forms
    assert (
        re.findall(
            r'<button type="button" hx-get="([^"]+)" hx-target="#mainModal">', nav
        )
        == forms
    )
