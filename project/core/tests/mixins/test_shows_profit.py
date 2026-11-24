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


@pytest.mark.parametrize(
    "owner_factory, balance_factory, owner_field, model",
    [
        pytest.param(
            SavingTypeFactory,
            SavingBalanceFactory,
            "saving_type",
            SavingBalance,
            id="savings",
        ),
        pytest.param(
            PensionTypeFactory,
            PensionBalanceFactory,
            "pension_type",
            PensionBalance,
            id="pensions",
        ),
    ],
)
def test_balance_property_and_q_agree(
    owner_factory, balance_factory, owner_field, model
):
    # every owner first: saving one resyncs the balance rows already made
    owners = [
        owner_factory(title=f"F{i}", closed=closed)
        for i, (*_, closed) in enumerate(SHAPES)
    ]
    for owner, (worth, since, sold, _closed) in zip(owners, SHAPES, strict=True):
        balance_factory(
            **{owner_field: owner},
            year=1999,
            market_value=worth,
            sold_since_check=since,
            sold=sold,
        )
    rows = list(model.objects.all())
    every = {row.pk for row in rows}
    shown = {row.pk for row in rows if row.shows_profit}

    assert shown
    assert every - shown
    assert (
        set(model.objects.filter(model.shows_profit_q()).values_list("pk", flat=True))
        == shown
    )
    assert (
        set(model.objects.exclude(model.shows_profit_q()).values_list("pk", flat=True))
        == every - shown
    )
