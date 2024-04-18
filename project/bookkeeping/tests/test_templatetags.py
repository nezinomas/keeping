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

    assert actual.replace("\n", "") == ""


def test_info_table_with_data_and_title(info_table):
    ctx = Context({"arr": {"data": [1], "title": ["xxx"]}})

    actual = info_table.render(ctx)

    assert "0,01" in actual
    assert "xxx" in actual


def test_info_table_highlight(info_table):
    ctx = Context({
        "arr": {
            "data": [1, -2],
            "title": ["x", "y"],
            "highlight": [True, True]
        }
    })

    actual = info_table.render(ctx).replace("\n", "")
    actual = ' '.join(actual.split())

    assert '<td class="table-success"> 0,01 </td>' in actual
    assert '<td class="table-danger"> -0,02 </td>' in actual


def test_info_table_for_calculate_debt_remains():
    template = Template("{% load slippers %}" "{% info_table data=arr calculate_debt_remains='true' %}")
    ctx = Context({"arr": {"data": [5, 3], "title": ["x", 'y']}})

    actual = template.render(ctx)

    assert "Liko grąžinti:  0,02" in actual
