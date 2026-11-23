import re

from ....core.tests.utils import render_cotton

# a month's row, each column its own figure in cents
ROW = {
    "incomes": 100,
    "expenses": 200,
    "balance": 300,
    "savings": 400,
    "savings_close": 500,
    "borrow": 600,
    "borrow_return": 700,
    "lend": 800,
    "lend_return": 900,
    "money_flow": 1000,
}


def test_a_month_row_draws_nothing_it_is_not_given():
    # the page's own values under the names the average row passes
    content = render_cotton(
        '<c-month-balance-row :row="row" />',
        row=ROW,
        blank_balance=True,
        end_label="page",
    )

    assert re.findall(r"<td[^>]*>([^<]*)</td>", content) == [
        "1,00",
        "2,00",
        "3,00",
        "4,00",
        "5,00",
        "6,00",
        "7,00",
        "8,00",
        "9,00",
        "10,00",
    ]
