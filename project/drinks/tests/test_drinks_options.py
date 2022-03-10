from ..lib.drinks_options import  DrinksOptions


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
