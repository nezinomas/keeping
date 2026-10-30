import pytest

from ...lib.daily_limit import DailyLimit


@pytest.mark.parametrize("amount", [0.0, -1.0])
def test_daily_limit_without_an_amount_raises(amount):
    with pytest.raises(ValueError):
        DailyLimit(amount)
