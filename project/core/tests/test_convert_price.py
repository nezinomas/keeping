import pytest

from ..lib.convert_price import float_to_int_cents, int_cents_to_float


@pytest.mark.parametrize(
    "price_float, expected_int",
    [
        (0.01, 1),  # Standard case
        (4669.73, 466973),  # Scenario 1: Exact two decimals
        (4669.736, 466973),  # Scenario 2: Truncation (discarding .006)
        (466.73, 46673),  # Known binary noise case
        (0.0, 0),  # Zero case
        (0.019, 1),  # Truncation verification
    ],
)
def test_float_to_int_conversion(price_float, expected_int):
    assert float_to_int_cents(price_float) == expected_int


@pytest.mark.parametrize(
    "cents_int, expected_float",
    [
        (1, 0.01),
        (466973, 4669.73),
        (46673, 466.73),
        (0, 0.0),
        (100, 1.0),
    ],
)
def test_int_cents_to_float_conversion(cents_int, expected_float):
    assert int_cents_to_float(cents_int) == expected_float
