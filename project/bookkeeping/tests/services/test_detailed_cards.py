import pytest

from ...services.detailed.cards import ExpenseCards, with_subtitles


def _table(title, rows):
    return {
        "title": title,
        "data": [{"title": name, "total_col": cents} for name, cents in rows],
        "total": {"total_col": sum(cents for _, cents in rows)},
    }


@pytest.fixture(name="tables")
def fixture_tables():
    return [
        _table("A", [("a1", 10000), ("a2", 20000)]),
        _table("B", [("b1", 50000), ("b2", 20000)]),
    ]


def test_no_tables_no_cards():
    assert ExpenseCards.build([]) == []


def test_two_cards_in_order(tables):
    titles = [card.title for card in ExpenseCards.build(tables)]

    assert titles == ["Didžiausia rūšis", "Didžiausia išlaida"]


def test_largest_type(tables):
    card = ExpenseCards.build(tables)[0]

    assert card.value == "B"
    assert card.note == "700 € · 70% metų sumos"
    assert len(card.explanation) == 1


def test_largest_expense(tables):
    card = ExpenseCards.build(tables)[1]

    assert card.value == "b1"
    assert card.note == "500 € · 50% · B"
    assert len(card.explanation) == 1


def test_largest_expense_thousands_separated():
    card = ExpenseCards.build([_table("A", [("a1", 123456700)])])[1]

    assert card.note.startswith("1")
    assert "1234567" not in card.note


def test_tie_takes_type_order_then_name():
    tables = [
        _table("Z", [("y", 100), ("x", 100)]),
        _table("A", [("a", 100)]),
    ]

    largest_type, largest_expense = ExpenseCards.build(tables)

    assert largest_type.value == "Z"
    assert largest_expense.value == "x"
    assert largest_expense.note.endswith("· Z")


def test_tie_is_stable_when_rows_are_reordered():
    rows = [("x", 100), ("y", 100)]

    forward = ExpenseCards.build([_table("A", rows)])[1]
    backward = ExpenseCards.build([_table("A", rows[::-1])])[1]

    assert forward == backward


def test_largest_expense_under_half_a_percent_never_reads_zero():
    tables = [_table(f"T{i:03}", [("n", 30000)]) for i in range(400)]

    card = ExpenseCards.build(tables)[1]

    assert card.note == "300 € · < 1% · T000"


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
    assert ExpenseCards.build(tables)[0].note == "8 € · 75% metų sumos"


def test_with_subtitles_keeps_the_tables_untouched(tables):
    with_subtitles(tables)

    assert "subtitle" not in tables[0]
