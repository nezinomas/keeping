from django.template.defaultfilters import floatformat

from ....core.lib.convert_price import int_cents_to_float
from ....core.lib.stat_card import EMPTY
from ...lib.calc_day_sum import DataDto, PlanCalculateDaySum
from ...services.cards import IncomeCards, SavingCards

ZERO_MONTHS = [0] * 12
MONTH_LEN = [{"month": m, "amount": 30} for m in range(1, 13)]


def _months(amounts):
    return [{"month": i + 1, "amount": amount} for i, amount in enumerate(amounts)]


def _data(incomes=ZERO_MONTHS, savings=ZERO_MONTHS):
    return DataDto(
        incomes=_months(incomes),
        expenses_regular=[],
        expenses_necessary=[],
        savings=_months(savings),
        per_day=[],
        necessary=[],
        month_len=MONTH_LEN,
    )


def _euro(cents):
    return floatformat(int_cents_to_float(cents), "0g")


# -------------------------------------------------------------------------------------
#                                                                               Pajamos
# -------------------------------------------------------------------------------------
def test_income_cards_titles_in_order():
    data = _data(incomes=[1000] * 12)

    cards = {card.title: card for card in IncomeCards.build(data)}

    assert list(cards) == ["Šiais metais", "Mėnesio mediana"]


def test_income_cards_this_year_is_the_year_total():
    incomes = [1000] * 12
    data = _data(incomes=incomes)

    card = {c.title: c for c in IncomeCards.build(data)}["Šiais metais"]

    assert card.value == _euro(sum(incomes))


def test_income_cards_median_equals_calc_day_sum_row_one():
    incomes = [1000] * 11 + [100_000]
    data = _data(incomes=incomes)

    expected = PlanCalculateDaySum(data).incomes_avg["1"]

    card = {c.title: c for c in IncomeCards.build(data)}["Mėnesio mediana"]

    assert card.value == _euro(expected)
    # median (1000) must differ from mean, so the test proves it reads the median
    assert expected != sum(incomes) / 12


def test_income_cards_are_empty_when_no_income_plans():
    data = _data(incomes=ZERO_MONTHS)

    cards = IncomeCards.build(data)

    assert [c.state for c in cards] == [EMPTY, EMPTY]
    assert all("0" not in c.value for c in cards)


# -------------------------------------------------------------------------------------
#                                                                              Taupymas
# -------------------------------------------------------------------------------------
def test_saving_cards_titles_in_order():
    data = _data(incomes=[100_000] * 12, savings=[25_000] * 12)

    cards = {card.title: card for card in SavingCards.build(data)}

    assert list(cards) == ["Šiais metais", "Planuotų pajamų dalis", "Per mėnesį"]


def test_saving_cards_this_year_is_the_year_total():
    savings = [25_000] * 12
    data = _data(incomes=[100_000] * 12, savings=savings)

    card = {c.title: c for c in SavingCards.build(data)}["Šiais metais"]

    assert card.value == _euro(sum(savings))


def test_saving_cards_share_of_planned_incomes():
    savings = [300_000] + [0] * 11
    incomes = [1_200_000] + [0] * 11
    data = _data(incomes=incomes, savings=savings)

    card = {c.title: c for c in SavingCards.build(data)}["Planuotų pajamų dalis"]

    assert card.value == "25"
    assert card.unit == "%"


def test_saving_cards_share_is_empty_without_income_plans():
    data = _data(incomes=ZERO_MONTHS, savings=[300_000] + [0] * 11)

    card = {c.title: c for c in SavingCards.build(data)}["Planuotų pajamų dalis"]

    assert card.state == EMPTY


def test_saving_cards_per_month_divides_the_year_total_by_twelve():
    data = _data(incomes=[1_200_000] * 12, savings=[1_000_000] + [0] * 11)

    card = {c.title: c for c in SavingCards.build(data)}["Per mėnesį"]

    assert card.value == "833"


def test_saving_cards_are_empty_when_no_saving_plans_even_with_incomes():
    data = _data(incomes=[1_200_000] * 12, savings=ZERO_MONTHS)

    cards = SavingCards.build(data)

    assert [c.state for c in cards] == [EMPTY, EMPTY, EMPTY]
    assert all("0" not in c.value for c in cards)
