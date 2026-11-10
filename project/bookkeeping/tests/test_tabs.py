from .. import views
from ..tabs import TABS


def test_each_tab_declares_its_title_url_and_template_in_nav_order():
    actual = [(tab.name, str(tab.title), tab.url, tab.template_name) for tab in TABS]

    assert actual == [
        (
            "incomes",
            "Pajamos",
            "/detailed/incomes/",
            "bookkeeping/detailed/tab_table.html",
        ),
        (
            "savings",
            "Taupymas",
            "/detailed/savings/",
            "bookkeeping/detailed/tab_table.html",
        ),
        (
            "expenses",
            "Išlaidos",
            "/detailed/expenses/",
            "bookkeeping/detailed/tab_expenses.html",
        ),
    ]


def test_the_default_tab_is_the_incomes_tab():
    assert views.DetailedTabMixin.default_tab is TABS["incomes"]
