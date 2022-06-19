from ..services.index import IndexService


def test_percentage_from_incomes():
    actual = IndexService.percentage_from_incomes(10, 1.5)

    assert actual == 15


def test_percentage_from_incomes_saving_none():
    actual = IndexService.percentage_from_incomes(10, None)

    assert not actual
