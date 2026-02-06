import pytest
from ..lib.convert_price import float_to_int_cents

@pytest.mark.parametrize(
    "price_float, expected_int",
    [
        (0.01, 1),           # Standard case
        (4669.73, 466973),   # Scenario 1: Exact two decimals
        (4669.736, 466973),  # Scenario 2: Truncation (discarding .006)
        (466.73, 46673),     # Known binary noise case
        (0.0, 0),            # Zero case
        (0.019, 1),          # Truncation verification
    ],
)
def test_float_to_int_conversion(price_float, expected_int):
    assert float_to_int_cents(price_float) == expected_int