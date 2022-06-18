from ..lib.view_index_helper import IndexHelper


def test_percentage_from_incomes():
    actual = IndexHelper.percentage_from_incomes(10, 1.5)

    assert actual == 15


def test_percentage_from_incomes_saving_none():
    actual = IndexHelper.percentage_from_incomes(10, None)

    assert not actual
