from ...services.keyword_match import KeywordMatcher, Match, NoMatch, normalise_keyword
from ..factories import ExpenseNameFactory, ExpenseTypeFactory


class FakeKeyword:
    def __init__(self, keyword, expense_name):
        self.keyword = keyword
        self.expense_name = expense_name


def test_normalise_keyword_strips_and_casefolds():
    assert normalise_keyword("  Jogurt ") == "jogurt"


def test_no_match_initial_is_empty():
    assert NoMatch().initial() == {}


def test_no_match_has_no_expense_name_attribute():
    assert not hasattr(NoMatch(), "expense_name")


def test_match_initial_holds_type_name_keyword():
    expense_type = ExpenseTypeFactory.build(title="Maistas")
    expense_name = ExpenseNameFactory.build(
        title="Pieno produktai", parent=expense_type
    )

    match = Match(keyword="jogurt", expense_name=expense_name)

    assert match.initial() == {
        "expense_type": expense_type,
        "expense_name": expense_name,
        "keyword": "jogurt",
    }


def test_keyword_matches_substring_ignoring_case():
    keywords = [FakeKeyword("jogurt", "Pieno produktai")]

    match = KeywordMatcher.match(
        "Natūralus VILVI jogurtas VILVI, 6 % rieb., 350 g", keywords
    )

    assert match.keyword == "jogurt"
    assert match.expense_name == "Pieno produktai"


def test_longest_keyword_wins():
    keywords = [
        FakeKeyword("varšk", "A"),
        FakeKeyword("varškės užtep", "B"),
    ]

    match = KeywordMatcher.match("Varškės užtepėlė su ...", keywords)

    assert match.keyword == "varškės užtep"


def test_equal_length_earliest_in_title_wins():
    keywords = [
        FakeKeyword("jogur", "A"),
        FakeKeyword("vilvi", "B"),
    ]

    match = KeywordMatcher.match(
        "Natūralus VILVI jogurtas VILVI, 6 % rieb., 350 g", keywords
    )

    assert match.keyword == "vilvi"


def test_diacritics_must_agree():
    keywords = [FakeKeyword("varsk", "A")]

    match = KeywordMatcher.match("Varškės užtepėlė", keywords)

    assert isinstance(match, NoMatch)


def test_no_keywords_returns_no_match():
    match = KeywordMatcher.match("Bananai, nuo 20 cm, 1 kg", [])

    assert isinstance(match, NoMatch)


def test_match_initial_type_is_the_names_own_among_same_titled_names():
    maistas = ExpenseTypeFactory.build(title="Maistas")
    buitines = ExpenseTypeFactory.build(title="Buitinės")
    ExpenseNameFactory.build(title="Kita", parent=maistas)
    kita = ExpenseNameFactory.build(title="Kita", parent=buitines)

    match = KeywordMatcher.match("Servetėlės", [FakeKeyword("servet", kita)])

    assert match.initial()["expense_type"] == buitines
    assert match.initial()["expense_name"] is kita
