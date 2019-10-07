import pytest

from .. import factories, models


def test_necessary_str():
    actual = factories.NecessaryPlan.build(year=2000, title='N')

    assert '2000/N' == str(actual)


@pytest.mark.django_db
@pytest.mark.xfail(raises=Exception)
def test_necessary_no_dublicates():
    factories.NecessaryPlan(year=2000, title='N')
    factories.NecessaryPlan(year=2000, title='N')
