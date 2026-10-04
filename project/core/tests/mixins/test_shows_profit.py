import pytest

from ....pensions.models import PensionBalance
from ....pensions.tests.factories import PensionBalanceFactory, PensionTypeFactory
from ....savings.models import SavingBalance
from ....savings.tests.factories import SavingBalanceFactory, SavingTypeFactory

pytestmark = pytest.mark.django_db

# (market_value, sold_since_check, sold, closed): every road to a shown row or not
SHAPES = [
    (100, 0, 0, None),
    (100, 40, 0, None),
    (0, 0, 0, None),
    (0, 40, 5, None),
    (0, 0, 5, 1999),
    (0, 0, 0, 1999),
    (0, 0, 5, 1998),
    (100, 40, 5, 1999),
    (100, 40, 5, 2000),
]


def _agree(model):
    rows = list(model.objects.all())
    shown = {row.pk for row in rows if row.shows_profit}

    assert {row.pk for row in rows} - shown
    assert shown
    assert (
        set(model.objects.filter(model.shows_profit_q()).values_list("pk", flat=True))
        == shown
    )
    assert (
        set(model.objects.exclude(model.shows_profit_q()).values_list("pk", flat=True))
        == {row.pk for row in rows} - shown
    )


def test_saving_balance_property_and_q_agree():
    funds = [
        SavingTypeFactory(title=f"F{i}", closed=closed)
        for i, (*_, closed) in enumerate(SHAPES)
    ]
    for fund, (worth, since, sold, _closed) in zip(funds, SHAPES, strict=True):
        SavingBalanceFactory(
            saving_type=fund,
            year=1999,
            market_value=worth,
            sold_since_check=since,
            sold=sold,
        )

    _agree(SavingBalance)


def test_pension_balance_property_and_q_agree():
    funds = [
        PensionTypeFactory(title=f"P{i}", closed=closed)
        for i, (*_, closed) in enumerate(SHAPES)
    ]
    for fund, (worth, since, sold, _closed) in zip(funds, SHAPES, strict=True):
        PensionBalanceFactory(
            pension_type=fund,
            year=1999,
            market_value=worth,
            sold_since_check=since,
            sold=sold,
        )

    _agree(PensionBalance)
