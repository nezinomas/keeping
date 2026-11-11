from .. import views
from ..tabs import TABS


def test_the_tabs_are_incomes_expenses_savings_and_day_in_nav_order():
    actual = [(tab.name, tab.url, tab.template_name) for tab in TABS]

    assert actual == [
        ("incomes", "/plans/incomes/", "plans/tab_incomes.html"),
        ("expenses", "/plans/expenses/", "plans/tab_expenses.html"),
        ("savings", "/plans/savings/", "plans/tab_savings.html"),
        ("day", "/plans/day/", "plans/tab_day.html"),
    ]
    assert views.TabViewMixin.default_tab is TABS["day"]
