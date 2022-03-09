from ..lib.drinks_options import  DrinksOptions


def test_to_beer():
    assert  DrinksOptions.to_beer(2.5) == 1


def test_to_wine():
    assert  DrinksOptions.to_wine(8) == 1


def test_to_vodka():
    assert  DrinksOptions.to_vodka(40) == 1


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
