import re

import pytest

from ....incomes.tests.factories import IncomeFactory
from ..helper import tab_table

pytestmark = pytest.mark.django_db


def test_wealth_table_shows_the_money_and_the_wealth(client_logged):
    IncomeFactory(price=100_000)

    table = tab_table(client_logged, "bookkeeping:tab_overview", "Turtas")

    assert re.findall(r"<th>\s*([^<]*?)\s*</th>", table) == ["Pinigai", "Turtas"]
    assert re.findall(r"<td>\s*([^<]*?)\s*</td>", table) == ["1.000,00", "1.000,00"]
