import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.template import loader
from django.test import RequestFactory
from hypothesis import example, given
from hypothesis import strategies as st


def _render_info_table(ctx, request):
    template = loader.get_template("cotton/info_table.html")

    return (
        HttpResponse(template.render(ctx, request))
        .content.decode("utf-8")
        .replace("\n", "")
        .replace("\t", "")
        .replace("  ", "")
    )


@pytest.fixture(name="info_table")
def fixture_info_table(fake_request):
    return lambda ctx: _render_info_table(ctx, fake_request)


INFO_TABLE_DATA = st.dictionaries(
    st.sampled_from(["data", "title", "xxx"]),
    st.one_of(st.none(), st.just(""), st.just([]), st.just("yyy")),
).filter(lambda data: not (data.get("title") and data.get("data")))


@given(ctx=st.one_of(st.just({}), INFO_TABLE_DATA.map(lambda data: {"data": data})))
@example(ctx={"data": {}})
@example(ctx={})
@example(ctx={"data": {"xxx": "yyy"}})
@example(ctx={"data": {"data": "yyy"}})
@example(ctx={"data": {"title": "yyy"}})
@example(ctx={"data": {"title": "", "data": ""}})
def test_info_table_without_a_title_or_without_data_renders_nothing(ctx):
    request = RequestFactory().get("/fake/")
    request.user = AnonymousUser()

    assert _render_info_table(ctx, request) == ""


def test_info_table_with_data_and_title(info_table):
    ctx = {"data": {"data": [1], "title": ["xxx"]}}

    actual = info_table(ctx)

    assert "0,01" in actual
    assert "xxx" in actual


def test_info_table_highlight(info_table):
    ctx = {"data": {"data": [1, -2], "title": ["x", "y"], "highlight": [True, True]}}

    actual = info_table(ctx)

    assert '<td data-sign="gain"> 0,01</td>' in actual
    assert '<td data-sign="loss"> -0,02</td>' in actual
    assert "table-success" not in actual
    assert "table-danger" not in actual


def test_info_table_for_calculate_debt_remains(info_table):
    ctx = {
        "data": {"data": [5, 3], "title": ["x", "y"]},
        "calculate_debt_remains": True,
    }

    actual = info_table(ctx)

    assert "Liko grąžinti:0,02" in actual
