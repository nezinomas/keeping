import pytest

from ..tabs import DETAILED_TABS, INDEX_TABS


@pytest.mark.parametrize(
    "tabs, expect",
    [
        pytest.param(
            DETAILED_TABS,
            [
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
            ],
            id="detailed",
        ),
        pytest.param(
            INDEX_TABS,
            [
                ("overview", "Apžvalga", "/", "bookkeeping/tab_overview.html"),
                (
                    "funds",
                    "Fondai",
                    "/bookkeeping/funds/",
                    "bookkeeping/tab_funds.html",
                ),
                (
                    "balance",
                    "Balansas",
                    "/bookkeeping/balance/",
                    "bookkeeping/tab_balance.html",
                ),
                (
                    "charts",
                    "Grafikai",
                    "/bookkeeping/charts/",
                    "bookkeeping/tab_charts.html",
                ),
            ],
            id="index",
        ),
    ],
)
def test_each_tab_declares_its_title_url_and_template_in_nav_order(tabs, expect):
    actual = [(tab.name, str(tab.title), tab.url, tab.template_name) for tab in tabs]

    assert actual == expect
