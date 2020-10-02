import pytest

from ..forms import SearchForm

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                  Search
# ---------------------------------------------------------------------------------------
def test_search_init(get_user):
    SearchForm()


def test_search_fields(get_user):
    form = SearchForm().as_p()

    assert '<input type="text" name="search"' in form


@pytest.mark.parametrize(
    'search',
    [
        ('xxx \''), ('xxx "'), ('xxx >'),
        ('xxx <'), ('xxx ?'), ('xxx \\'),
        ('xxx |'), ('xxx {'), ('xxx }'),
        ('xxx ]'), ('xxx ['), ('xxx ~'),
        ('xxx `'), ('xxx !'), ('xxx @'),
        ('xxx #'), ('xxx $'), ('xxx %'),
        ('xxx ^'), ('xxx &'), ('xxx *'),
        ('xxx ('), ('xxx )'), ('xxx +'),
        ('xxx ='), ('xxx ;'), ('xxx ,'),
        ('xxx /'), ('x'*3), ('x'*51),
    ]
)
def test_search_form_invalid(search):
    form = SearchForm(data={'search': search})

    assert not form.is_valid()


@pytest.mark.parametrize(
    'search',
    [
        ('2000'),
        ('2000.01'),
        ('2000-01'),
        ('2000.01.01'),
        ('2000-01-01'),
        ('2000 test'),
        ('2000 test1 test2'),
        ('test'),
        ('test1 test2'),
    ]
)
def test_search_form_valid(search):
    form = SearchForm(data={'search': search})

    assert form.is_valid()
