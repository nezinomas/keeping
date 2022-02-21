import pytest
from django.template import Context, Template


@pytest.fixture
def _info_table():
    template = Template(
        '{% load tables %}'
        '{% info_table arr %}'
    )
    return template


@pytest.fixture
def _funds_table():
    template = Template(
        '{% load tables %}'
        '{% funds_table arr %}'
    )
    return template



@pytest.mark.parametrize('arr', [({'arr': {}}), ({}), ({'arr': {'xxx': 'yyy'}})])
def test_info_table_no_data(_info_table, arr):
    ctx = Context(arr)

    actual = _info_table.render(ctx)

    assert actual == '\n'


def test_info_table_with_data(_info_table):
    ctx = Context({'arr': {'data': [66]}})

    actual = _info_table.render(ctx)

    assert '66,0' in actual


def test_info_table_with_data_and_title(_info_table):
    ctx = Context({'arr': {'data': [66], 'title': ['xxx']}})

    actual = _info_table.render(ctx)

    assert '66,0' in actual
    assert 'xxx' in actual


@pytest.mark.parametrize('arr', [({'arr': {}}), ({}), ({'arr': {'xxx': 'yyy'}})])
def test_funds_table_no_data(_funds_table, arr):
    ctx = Context(arr)

    actual = _funds_table.render(ctx)

    assert actual == '\n'


def test_funds_table_with_data(_funds_table):
    ctx = Context({
        'arr': {
            'title': 'Xxx',
            'items': [{
                'past_amount': 1,
                'past_fee': 2,
                'incomes': 3,
                'fee': 4,
                'invested': 5,
                'market_value': 6,
                'profit_incomes_sum': 7,
                'profit_incomes_proc': 8,
                'profit_invested_sum': 9,
                'profit_invested_proc': 10}],
            'total_row': {
                'past_amount': 11,
                'past_fee': 12,
                'incomes': 13,
                'fee': 14,
                'invested': 15,
                'market_value': 16,
                'profit_incomes_sum': 17,
                'profit_invested_sum': 18,
            },
            'profit_incomes_proc': 19,
            'profit_invested_proc': 20,
            'percentage_from_incomes': 21,
        }}
    )

    actual = _funds_table.render(ctx)

    assert 'Xxx' in actual  # title
    assert '21,0' in actual  # percentage_from_incomes

    for i in range(1, 21):
        assert f'{i},00' in actual
