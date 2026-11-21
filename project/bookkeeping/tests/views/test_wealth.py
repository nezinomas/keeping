from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ....core.tests.utils import tab_fragment
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.tests.factories import SavingTypeFactory
from ..factories import AccountWorthFactory, PensionWorthFactory
from ..helper import quiet_build, tab_cards
from ..signals.helpers import buy, worth

pytestmark = pytest.mark.django_db


def _wealth_and_averages():
    """Each figure its own, so a Card that reads another's shows."""
    # the accounts end at 4 800,00 - 1 000,00 = 3 800,00; their Worth is not read
    IncomeFactory(price=500000)
    ExpenseFactory(price=20000)
    # the next year's money and fund differ, so a figure read for the wrong year shows
    IncomeFactory(date=date(2000, 1, 1), price=7000)
    AccountWorthFactory(price=390000)
    fund = SavingTypeFactory()
    buy(fund, 100000)
    worth(fund, 130000)
    worth(fund, 150000, year=2000)
    pension = PensionTypeFactory()
    PensionFactory(pension_type=pension, price=60000, fee=0)
    PensionWorthFactory(pension_type=pension, price=70000)


# one month holds the year's 5 000,00 in and 200,00 out; an average divides them by
# the months reached, and a year not started draws its wealth and its averages empty
@pytest.mark.parametrize(
    "today, averages",
    [
        pytest.param("2000-06-01", ["417", "17"], id="past-of-twelve"),
        pytest.param("1999-06-01", ["833", "33"], id="running-of-six"),
        pytest.param("1998-06-01", ["&mdash;", "&mdash;"], id="not-started"),
    ],
)
def test_apzvalga_cards_read_the_wealth_and_the_averages(
    client_logged, main_user, today, averages
):
    with quiet_build(main_user):
        _wealth_and_averages()

    with time_machine.travel(today, tick=False):
        content = tab_fragment(client_logged, reverse("bookkeeping:tab_overview"))

    assert [(label, figure) for label, figure, _note, _state in tab_cards(content)] == [
        ("Pinigai", "5.100"),
        ("Turtas", "5.800"),
        ("Vidutinės pajamos", averages[0]),
        ("Vidutinės išlaidos", averages[1]),
    ]
