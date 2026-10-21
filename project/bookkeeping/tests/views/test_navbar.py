import re

import pytest
from django.urls import reverse

from ....counts.tests.factories import CountTypeFactory

pytestmark = pytest.mark.django_db


def _active_links(client, path: str) -> list[str]:
    content = client.get(path).content.decode()

    return re.findall(r'<div class="active">\s*<a href="([^"]+)"', content)


@pytest.mark.parametrize(
    "path",
    ["/detailed/", "/detailed/incomes/", "/detailed/savings/", "/detailed/expenses/"],
)
def test_the_navbar_marks_detailed_on_every_tab(client_logged, path):
    assert _active_links(client_logged, path) == [reverse("bookkeeping:detailed")]


def test_the_navbar_still_marks_expenses_on_expenses(client_logged):
    assert _active_links(client_logged, "/expenses/") == [reverse("expenses:index")]


@pytest.mark.parametrize(
    "path, url_name",
    [
        ("/", "bookkeeping:index"),
        ("/month/", "bookkeeping:month"),
        ("/incomes/", "incomes:index"),
        ("/transactions/", "transactions:index"),
        ("/savings/", "savings:index"),
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


def test_the_navbar_menus_without_a_page_stay_unlinked_where_a_page_has_a_url(
    client_logged, main_user
):
    # Books' Duomenys passes its own `url` to the page's context
    content = client_logged.get(reverse("books:tab_data", args=["all"])).content
    nav = re.search(r'<nav id="main-nav">.*?</nav>', content.decode(), re.S).group()

    assert re.findall(r"<div>\s*<span>\s*([^<]+?)\s*</span>", nav) == [
        "Pridėti",
        main_user.username,
    ]
