import pytest

from ...services.detailed.shares import with_subtitles


def _table(title, rows):
    return {"title": title, "total": {"total_col": sum(cents for _, cents in rows)}}


@pytest.fixture(name="tables")
def fixture_tables():
    return [
        _table("A", [("a1", 10000), ("a2", 20000)]),
        _table("B", [("b1", 50000), ("b2", 20000)]),
    ]


def test_subtitles_are_the_shares(tables):
    subtitled = with_subtitles(tables)

    assert [table["subtitle"] for table in subtitled] == [
        "30% metų sumos",
        "70% metų sumos",
    ]


def test_subtitle_under_half_a_percent_never_reads_zero():
    tables = [_table("A", [("a", 300)]), _table("B", [("b", 99700)])]

    assert with_subtitles(tables)[0]["subtitle"] == "< 1% metų sumos"


def test_denominator_is_the_sum_of_every_type_total():
    tables = [_table("A", [("a", 250)]), _table("B", [("b", 750)])]

    assert [t["subtitle"] for t in with_subtitles(tables)] == [
        "25% metų sumos",
        "75% metų sumos",
    ]


def test_with_subtitles_keeps_the_tables_untouched(tables):
    with_subtitles(tables)

    assert "subtitle" not in tables[0]
