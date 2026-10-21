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


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (250, 750, ["25% metų sumos", "75% metų sumos"]),
        (1, 9999, ["< 1% metų sumos", "> 99% metų sumos"]),
    ],
    ids=["of_every_type_total", "never_nothing_or_the_whole"],
)
def test_a_subtitle_is_its_share_of_every_type_total(a, b, expected):
    tables = [_table("A", [("a", a)]), _table("B", [("b", b)])]

    assert [t["subtitle"] for t in with_subtitles(tables)] == expected


def test_with_subtitles_keeps_the_tables_untouched(tables):
    with_subtitles(tables)

    assert "subtitle" not in tables[0]
