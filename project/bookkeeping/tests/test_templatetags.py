import pytest
from django.template import Context, Template


@pytest.fixture(name="info_table")
def fixture_info_table():
    return Template("{% load slippers %}" "{% info_table data=arr %}")


@pytest.mark.parametrize(
    "arr",
    [
        ({"arr": {}}),
        ({}),
        ({"arr": {"xxx": "yyy"}}),
        ({"arr": {"data": "yyy"}}),
        ({"arr": {"title": "yyy"}}),
        ({"arr": {"title": "", "data": ""}}),
    ]
)
def test_info_table_no_data(info_table, arr):
    ctx = Context(arr)

    actual = info_table.render(ctx)

    assert actual == "\n\n\n\n\n\n"


def test_info_table_with_data_and_title(info_table):
    ctx = Context({"arr": {"data": [1], "title": ["xxx"]}})

    actual = info_table.render(ctx)

    assert "0,01" in actual
    assert "xxx" in actual
