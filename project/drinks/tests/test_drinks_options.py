import pytest

from ..lib.drinks_options import DrinksOptions


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 1 / 2.5),
        ('wine', 1 / 8),
        ('vodka', 1 / 40),
        ('stdav', 1),
        ('xxx', 1),
    ]
)
def test_ratio(drink_type, expect):
    actual = DrinksOptions(drink_type=drink_type).ratio

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, ml, expect',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 10, 1),
        ('xxx', 500, 500),
    ]
)
def test_ml_to_stdav(drink_type, ml, expect):
    actual = DrinksOptions().ml_to_stdav(drink_type=drink_type, ml=ml)

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, ml, expect',
    [
        ('beer', 500, 2.5),
        ('wine', 750, 8),
        ('vodka', 1000, 40),
        ('stdav', 10, 1),
        ('xxx', 500, 500),
    ]
)
def test_ml_to_stdav_01(drink_type, ml, expect):
    actual = DrinksOptions(drink_type).ml_to_stdav(ml)

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, stdav, expect',
    [
        ('beer', 2.5, 500),
        ('wine', 8, 750),
        ('vodka', 40, 1000),
        ('stdav', 1, 10),
    ]
)
def test_stdav_to_ml(drink_type, stdav, expect):
    actual = DrinksOptions().stdav_to_ml(drink_type=drink_type, stdav=stdav)

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, stdav, expect',
    [
        ('beer', 2.5, 500),
        ('wine', 8, 750),
        ('vodka', 40, 1000),
        ('stdav', 1, 10),
    ]
)
def test_stdav_to_ml_01(drink_type, stdav, expect):
    actual = DrinksOptions(drink_type).stdav_to_ml(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 1 / 2.5),
        ('wine', 1 / 8),
        ('vodka', 1 / 40),
        ('stdav', 1),
        ('xxx', 1),
    ]
)
def test_ratio_drink_type_from_user(drink_type, expect):
    actual = DrinksOptions(drink_type=drink_type).ratio

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 2.5),
        ('wine', 8),
        ('vodka', 40),
        ('stdav', 1),
        ('xxx', 1),
    ]
)
def test_stdav(drink_type, expect):
    actual = DrinksOptions(drink_type=drink_type).stdav

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, expect',
    [
        ('beer', 2.5),
        ('wine', 8),
        ('vodka', 40),
        ('stdav', 1),
        ('xxx', 1),
    ]
)
def test_stdav_drink_type_from_user(drink_type, expect):
    actual = DrinksOptions(drink_type=drink_type).stdav

    assert actual == expect


@pytest.mark.parametrize(
    'qty, from_, to, expect',
    [
        (1, 'beer', 'beer', 1),
        (1, 'beer', 'wine', 0.31),
        (1, 'beer', 'vodka', 0.06),
        (1, 'beer', 'stdav', 2.5),
        (1, 'wine', 'beer', 3.2),
        (1, 'wine', 'wine', 1),
        (1, 'wine', 'vodka', 0.2),
        (1, 'wine', 'stdav', 8),
        (1, 'vodka', 'beer', 16),
        (1, 'vodka', 'wine', 5),
        (1, 'vodka', 'vodka', 1),
        (1, 'vodka', 'stdav', 40),
    ]
)
def test_convert(qty, from_, to, expect):
    actual = DrinksOptions(from_).convert(qty, to)
    round(actual, 2) == expect


@pytest.mark.parametrize(
    'qty, from_, to, expect',
    [
        (1, 'beer', 'beer', 1),
        (1, 'beer', 'wine', 0.31),
        (1, 'beer', 'vodka', 0.06),
        (1, 'beer', 'stdav', 2.5),
        (1, 'wine', 'beer', 3.2),
        (1, 'wine', 'wine', 1),
        (1, 'wine', 'vodka', 0.2),
        (1, 'wine', 'stdav', 8),
        (1, 'vodka', 'beer', 16),
        (1, 'vodka', 'wine', 5),
        (1, 'vodka', 'vodka', 1),
        (1, 'vodka', 'stdav', 40),
    ]
)
def test_convert_from_user(qty, from_, to, expect, get_user):
    get_user.drink_type = from_

    actual = DrinksOptions().convert(qty, to)
    round(actual, 2) == expect


@pytest.mark.parametrize(
    'drink_type, stdav, expect',
    [
        ('beer', 2.5, 0.025),
        ('wine', 8, 0.08),
        ('vodka', 40, 0.4),
        ('stdav', 1, 0.01),
    ]
)
def test_stdav_to_alkohol(drink_type, stdav, expect, get_user):
    get_user.drink_type = drink_type

    actual = DrinksOptions().stdav_to_alkohol(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, stdav, expect',
    [
        ('beer', 2.5, 0.025),
        ('wine', 8, 0.08),
        ('vodka', 40, 0.4),
        ('stdav', 1, 0.01),
    ]
)
def test_stdav_to_alkohol_01(drink_type, stdav, expect):
    actual = DrinksOptions(drink_type).stdav_to_alkohol(stdav)

    assert actual == expect


@pytest.mark.parametrize(
    'drink_type, year, stdav, expect',
    [
        ('beer', 1999, 2.5, 365),
        ('wine', 1999, 8, 365),
        ('vodka', 1999, 40, 365),
        ('stdav', 1999, 1, 365),
    ]
)
def test_stdav_to_bottles(drink_type, year, stdav, expect, get_user):
    get_user.drink_type = drink_type

    actual = DrinksOptions().stdav_to_bottles(year=year, max_stdav=stdav)

    assert actual == expect
