import pytest
from django.template import Context, Template

@pytest.fixture
def _info_table():
    template = Template(
        '{% load tables %}'
        '{% info_table arr %}'
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
