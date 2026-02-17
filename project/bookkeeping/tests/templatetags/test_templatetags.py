import pytest
from django.http import HttpResponse
from django.template import loader


@pytest.fixture(name="info_table")
def fixture_info_table(fake_request):
    def _func(ctx):
        template = loader.get_template("cotton/info_table.html")

        return (
            HttpResponse(template.render(ctx, fake_request))
            .content.decode("utf-8")
            .replace("\n", "")
            .replace("\t", "")
            .replace("  ", "")
        )

    return _func


@pytest.mark.parametrize(
    "ctx",
    [
        ({"data": {}}),
        ({}),
        ({"data": {"xxx": "yyy"}}),
        ({"data": {"data": "yyy"}}),
        ({"data": {"title": "yyy"}}),
        ({"data": {"title": "", "data": ""}}),
    ],
)
def test_info_table_no_data(info_table, ctx):
    actual = info_table(ctx)

    assert actual == ""


def test_info_table_with_data_and_title(info_table):
    ctx = {"data": {"data": [1], "title": ["xxx"]}}

    actual = info_table(ctx)

    assert "0,01" in actual
    assert "xxx" in actual


def test_info_table_highlight(info_table):
    ctx = {"data": {"data": [1, -2], "title": ["x", "y"], "highlight": [True, True]}}

    actual = info_table(ctx)

    assert '<td class="table-success"> 0,01</td>' in actual
    assert '<td class="table-danger"> -0,02</td>' in actual


def test_info_table_for_calculate_debt_remains(info_table):
    ctx = {
        "data": {"data": [5, 3], "title": ["x", "y"]},
        "calculate_debt_remains": True,
    }

    actual = info_table(ctx)

    assert "Liko grąžinti:0,02" in actual
