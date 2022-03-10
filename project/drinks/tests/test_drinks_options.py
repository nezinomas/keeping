from ..lib.drinks_options import  DrinksOptions
import pytest

def test_std_to_beer():
    assert  DrinksOptions.std_to_beer(2.5) == 1


def test_beer_to_std():
    assert  DrinksOptions.beer_to_std(1) == 2.5


def test_std_to_wine():
    assert  DrinksOptions.std_to_wine(8) == 1


def test_wine_to_std():
    assert  DrinksOptions.wine_to_std(1) == 8


def test_std_to_vodka():
    assert  DrinksOptions.std_to_vodka(40) == 1


def test_vodka_to_std():
    assert  DrinksOptions.vodka_to_std(1) == 40


def test_get_ratio_for_beer(get_user):
    get_user.drink_type = 'beer'

    assert DrinksOptions().ratio == 1 / 2.5


def test_get_ratio_for_wine(get_user):
    get_user.drink_type = 'wine'

    assert DrinksOptions().ratio == 1 / 8


def test_get_ratio_for_vodka(get_user):
    get_user.drink_type = 'vodka'

    assert DrinksOptions().ratio == 1 / 40


def test_get_ratio_for_std_av(get_user):
    get_user.drink_type = 'std_av'

    assert DrinksOptions().ratio == 1


def test_get_ratio_for_beer_set_in_init():
    assert DrinksOptions('beer').ratio == 1 / 2.5


def test_get_ratio_for_wine_set_in_init():
    assert DrinksOptions('wine').ratio == 1 / 8


def test_get_ratio_for_vodka_set_in_init():
    assert DrinksOptions('vodka').ratio == 1 / 40


def test_get_ratio_for_std_av_set_in_init():
     assert DrinksOptions('std_av').ratio == 1


def test_get_stdav_for_beer(get_user):
    get_user.drink_type = 'beer'

    assert DrinksOptions().stdav == 2.5


def test_get_stdav_for_wine(get_user):
    get_user.drink_type = 'wine'

    assert DrinksOptions().stdav == 8


def test_get_stdav_for_vodka(get_user):
    get_user.drink_type = 'vodka'

    assert DrinksOptions().stdav == 40


def test_get_stdav_for_std_av(get_user):
    get_user.drink_type = 'std_av'

    assert DrinksOptions().stdav == 1


def test_get_stdav_for_beer_set_in_init():
    assert DrinksOptions('beer').stdav == 2.5


def test_get_stdav_for_wine_set_in_init():
    assert DrinksOptions('wine').stdav == 8


def test_get_stdav_for_vodka_set_in_init():
    assert DrinksOptions('vodka').stdav == 40


def test_get_stdav_for_std_av_set_in_init():
     assert DrinksOptions('std_av').stdav == 1


@pytest.mark.parametrize(
    'qty, from_, to, expect',
    [
        (1, 'beer', 'beer', 1),
        (1, 'beer', 'wine', 0.31),
        (1, 'beer', 'vodka', 0.06),
        (1, 'wine', 'beer', 3.2),
        (1, 'wine', 'wine', 1),
        (1, 'wine', 'vodka', 0.2),
        (1, 'vodka', 'beer', 16),
        (1, 'vodka', 'wine', 5),
        (1, 'vodka', 'vodka', 1),
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
        (1, 'wine', 'beer', 3.2),
        (1, 'wine', 'wine', 1),
        (1, 'wine', 'vodka', 0.2),
        (1, 'vodka', 'beer', 16),
        (1, 'vodka', 'wine', 5),
        (1, 'vodka', 'vodka', 1),
    ]
)
def test_convert(qty, from_, to, expect, get_user):
    get_user.drink_type = from_

    actual = DrinksOptions().convert(qty, to)
    round(actual, 2) == expect
