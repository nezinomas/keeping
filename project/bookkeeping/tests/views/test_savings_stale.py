import pytest

from ....savings.tests.factories import SavingTypeFactory
from ....users.models import User
from ..helper import (
    KINDS,
    funds_table,
    quiet_build,
    row_cells,
    stale_fund,
    switch_a_into_b,
    total_cells,
)
from ..signals.helpers import YEAR, buy, sell, worth

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "title, kind, year, later_worths, cells",
    [
        pytest.param("Fondai", "funds", YEAR, [], ["1.000,00", "-", "-"], id="funds"),
        pytest.param(
            "Pensijos", "pensions", YEAR, [], ["1.000,00", "-", "-"], id="pensions"
        ),
        pytest.param(
            "Fondai", "funds", YEAR + 1, [], ["1.000,00", "-", "-"], id="next-year"
        ),
        pytest.param(
            "Fondai",
            "funds",
            YEAR,
            [70000],
            ["700,00", "100,00", "10,00%"],
            id="fresh",
        ),
    ],
)
def test_the_worth_shows_and_the_profit_reads_dashes_until_a_worth_after_the_sell(
    client_logged, main_user, title, kind, year, later_worths, cells
):
    with quiet_build(main_user):
        fund = stale_fund(kind=kind)
        for price in later_worths:
            worth(fund, price)
    User.objects.update(year=year)

    assert row_cells(funds_table(client_logged, title), "Stale")[9:12] == cells


@pytest.mark.parametrize("title, kind", KINDS)
def test_the_total_transferred_sums_every_row_its_profit_and_percent_only_the_shown(
    client_logged, main_user, title, kind
):
    with quiet_build(main_user):
        a = SavingTypeFactory(title="A", type=kind)
        b = SavingTypeFactory(title="B", type=kind)
        buy(a, 100000)
        worth(a, 110000)
        buy(b, 50000)
        sell(b, 10000)

    cells = total_cells(funds_table(client_logged, title))

    assert cells[5] == "1.500,00"
    assert cells[-2:] == ["100,00", "10,00%"]


def test_a_switch_out_of_a_stale_fund_leaves_the_base_of_the_fund_that_shows(
    client_logged, main_user
):
    with quiet_build(main_user):
        switch_a_into_b()

    cells = total_cells(funds_table(client_logged))

    assert cells[5] == "2.300,00"
    assert cells[-2:] == ["100,00", "7,69%"]
