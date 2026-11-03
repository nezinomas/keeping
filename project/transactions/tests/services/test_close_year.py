from datetime import date

import pytest

from ....core.tests.utils import count_queries
from ....savings.tests.factories import SavingTypeFactory
from ...services.close_year import FundCloseYear
from ..factories import SavingChangeFactory, SavingCloseFactory

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("quiet_syncs")]


@pytest.mark.parametrize(
    "closed, day, closes",
    [
        pytest.param(1999, date(1999, 6, 1), True, id="closing_move"),
        pytest.param(1999, date(1999, 1, 1), False, id="earlier_move"),
        pytest.param(None, date(1999, 6, 1), False, id="open_fund"),
    ],
)
def test_a_loaded_fund_closes_as_is_closing_move(closed, day, closes):
    fund = SavingTypeFactory(closed=closed)
    SavingCloseFactory(from_account=fund, date=date(1999, 1, 1))
    SavingChangeFactory(from_account=fund, date=date(1999, 6, 1))

    loaded = FundCloseYear.of_funds([fund.pk])[fund.pk]

    assert loaded.closes(day) == FundCloseYear.is_closing_move(fund.pk, day) == closes


def test_of_funds_query_count():
    def queries(funds):
        pks = []
        for n in range(funds):
            fund = SavingTypeFactory(title=f"Fund {funds}-{n}", closed=1999)
            SavingCloseFactory(from_account=fund)
            pks.append(fund.pk)

        def closes():
            for close_year in FundCloseYear.of_funds(pks).values():
                close_year.closes(date(1999, 1, 1))

        return count_queries(closes)

    assert queries(2) == queries(6)
