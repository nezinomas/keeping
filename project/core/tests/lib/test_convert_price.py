from types import SimpleNamespace

import pytest

from ...lib.convert_price import (
    ConvertPriceMixin,
    float_to_int_cents,
    int_cents_to_float,
)


@pytest.mark.parametrize(
    "price_float, expected_int",
    [
        (0.01, 1),  # Standard case
        (4669.73, 466973),  # Scenario 1: Exact two decimals
        (4669.736, 466973),  # Scenario 2: Truncation (discarding .006)
        (466.73, 46673),  # Known binary noise case
        (0.0, 0),  # Zero case
        (0.019, 1),  # Truncation verification
        (None, 0),
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


class DummyClassForConvertPriceMixin:
    def get_object(self):
        pass

    def clean(self):
        pass


@pytest.mark.parametrize(
    "cents, expected_float",
    [
        (466973, 4669.73),
        (100, 1.0),
        (0, 0),  # Note: 0 remains 0 if using the walrus operator check
    ],
)
def test_covert_to_price_mixin_has_fields(mocker, cents, expected_float):
    mock_obj = SimpleNamespace(price=cents, fee=cents)
    mocker.patch.object(
        DummyClassForConvertPriceMixin, "get_object", return_value=mock_obj
    )

    class DummyClass(ConvertPriceMixin, DummyClassForConvertPriceMixin):
        pass

    view = DummyClass()
    result = view.get_object()

    assert result.price == expected_float
    assert result.fee == expected_float


def test_covert_to_price_mixin_missing_fields(mocker):
    mock_obj = SimpleNamespace(price=1000)
    mocker.patch.object(
        DummyClassForConvertPriceMixin, "get_object", return_value=mock_obj
    )

    class DummyClass(ConvertPriceMixin, DummyClassForConvertPriceMixin):
        pass

    view = DummyClass()
    result = view.get_object()

    assert result.price == 10.0  # Converted
    assert not hasattr(result, "fee")  # Still doesn't exist, didn't crash


def test_covert_to_price_mixin_merges_fields(mocker):
    class DummyClass(ConvertPriceMixin, DummyClassForConvertPriceMixin):
        price_fields = ["new_field"]

    mock_obj = SimpleNamespace(price=1000, fee=2000, new_field=3000)
    mocker.patch.object(
        DummyClassForConvertPriceMixin, "get_object", return_value=mock_obj
    )

    view = DummyClass()
    result = view.get_object()

    assert result.new_field == 30.0

    assert result.price == 10.0
    assert result.fee == 20.0


@pytest.mark.parametrize(
    "price, expected_int",
    [
        (0.01, 1),  # Standard case
        (4669.73, 466973),  # Scenario 1: Exact two decimals
        (4669.736, 466973),  # Scenario 2: Truncation (discarding .006)
        (466.73, 46673),  # Known binary noise case
        (0.0, 0),  # Zero case
        (0.019, 1),  # Truncation verification
        (None, None),
    ],
)
def test_convert_to_cents_mixin_has_fields(mocker, price, expected_int):
    mock_obj = {"price": price, "fee": price}
    mocker.patch.object(DummyClassForConvertPriceMixin, "clean", return_value=mock_obj)

    class DummyClass(ConvertPriceMixin, DummyClassForConvertPriceMixin):
        pass

    view = DummyClass()
    result = view.clean()

    assert result["price"] == expected_int
    assert result["fee"] == expected_int


def test_covert_to_cents_mixin_merges_fields(mocker):
    class DummyClass(ConvertPriceMixin, DummyClassForConvertPriceMixin):
        price_fields = ["new_field"]

    mock_obj = {"price": 1, "fee": 2, "new_field": 3}
    mocker.patch.object(DummyClassForConvertPriceMixin, "clean", return_value=mock_obj)

    view = DummyClass()
    result = view.clean()

    assert result["price"] == 100
    assert result["fee"] == 200
    assert result["new_field"] == 300
