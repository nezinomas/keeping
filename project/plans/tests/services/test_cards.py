import pytest
from django.db import connection
from django.template.defaultfilters import floatformat
from django.test.utils import CaptureQueriesContext

from ....core.lib.convert_price import int_cents_to_float
from ....core.lib.stat_card import EMPTY, HIGH, NEUTRAL
from ...lib.calc_day_sum import DataDto, PlanCalculateDaySum, PlanCollectData
from ...services.cards import DayCards, ExpenseCards, IncomeCards, SavingCards
from ..factories import ExpensePlanFactory, NecessaryPlanFactory

ZERO_MONTHS = [0] * 12
MONTH_LEN = [{"month": m, "amount": 30} for m in range(1, 13)]


def _months(amounts):
    return [{"month": i + 1, "amount": amount} for i, amount in enumerate(amounts)]


def _data(
    incomes=ZERO_MONTHS,
    savings=ZERO_MONTHS,
    expenses_regular=ZERO_MONTHS,
    expenses_necessary=ZERO_MONTHS,
    necessary=ZERO_MONTHS,
    per_day=(),
):
    return DataDto(
        incomes=_months(incomes),
        expenses_regular=_months(expenses_regular),
        expenses_necessary=_months(expenses_necessary),
        savings=_months(savings),
        per_day=_months(per_day),
        necessary=_months(necessary),
        month_len=MONTH_LEN,
    )


def _card(cards, title):
    return {card.title: card for card in cards}[title]


def _euro(cents):
    return floatformat(int_cents_to_float(cents), "0g")


def _euro_cents(cents):
    return floatformat(int_cents_to_float(cents), "2g")


# Pajamos
def test_income_cards_titles_in_order():
    data = _data(incomes=[1000] * 12)

    cards = {card.title: card for card in IncomeCards.build(data)}

    assert list(cards) == ["Per metus", "Mėnesio mediana"]


def test_income_cards_per_year_is_the_year_total():
    incomes = [1000] * 12
    data = _data(incomes=incomes)

    card = _card(IncomeCards.build(data), "Per metus")

    assert card.value == _euro(sum(incomes))


def test_income_cards_median_equals_calc_day_sum_row_one():
    incomes = [1000] * 11 + [100_000]
    data = _data(incomes=incomes)

    expected = PlanCalculateDaySum(data).incomes_avg["1"]

    card = _card(IncomeCards.build(data), "Mėnesio mediana")

    assert card.value == _euro(expected)
    # median (1000) must differ from mean, so the test proves it reads the median
    assert expected != sum(incomes) / 12


def test_income_cards_are_empty_when_no_income_plans():
    data = _data(incomes=ZERO_MONTHS)

    cards = IncomeCards.build(data)

    assert [c.state for c in cards] == [EMPTY, EMPTY]
    assert all("0" not in c.value for c in cards)


# Taupymas
def test_saving_cards_titles_in_order():
    data = _data(incomes=[100_000] * 12, savings=[25_000] * 12)

    cards = {card.title: card for card in SavingCards.build(data)}

    assert list(cards) == ["Per metus", "Planuotų pajamų dalis", "Per mėnesį"]


def test_saving_cards_per_year_is_the_year_total():
    savings = [25_000] * 12
    data = _data(incomes=[100_000] * 12, savings=savings)

    card = _card(SavingCards.build(data), "Per metus")

    assert card.value == _euro(sum(savings))


def test_saving_cards_share_of_planned_incomes():
    savings = [300_000] + [0] * 11
    incomes = [1_200_000] + [0] * 11
    data = _data(incomes=incomes, savings=savings)

    card = _card(SavingCards.build(data), "Planuotų pajamų dalis")

    assert card.value == "25"
    assert card.unit == "%"


def test_saving_cards_share_is_empty_without_income_plans():
    data = _data(incomes=ZERO_MONTHS, savings=[300_000] + [0] * 11)

    card = _card(SavingCards.build(data), "Planuotų pajamų dalis")

    assert card.state == EMPTY


def test_saving_cards_per_month_divides_the_year_total_by_twelve():
    data = _data(incomes=[1_200_000] * 12, savings=[1_000_000] + [0] * 11)

    card = _card(SavingCards.build(data), "Per mėnesį")

    assert card.value == "833"


def test_saving_cards_are_empty_when_no_saving_plans_even_with_incomes():
    data = _data(incomes=[1_200_000] * 12, savings=ZERO_MONTHS)

    cards = SavingCards.build(data)

    assert [c.state for c in cards] == [EMPTY, EMPTY, EMPTY]
    assert all("0" not in c.value for c in cards)


# Išlaidos
EXPENSES_REGULAR = [1000] * 12
EXPENSES_NECESSARY = [500] * 12
NECESSARY = [200] * 12


@pytest.fixture
def mixed_expenses():
    return _data(
        expenses_regular=EXPENSES_REGULAR,
        expenses_necessary=EXPENSES_NECESSARY,
        necessary=NECESSARY,
        savings=[100] * 12,
    )


def test_expense_cards_titles_in_order(mixed_expenses):
    cards = {card.title: card for card in ExpenseCards.build(mixed_expenses)}

    assert list(cards) == ["Per metus", "Būtinos", "Kasdienės", "Per mėnesį"]


def test_expense_cards_per_year_is_expense_and_necessary_plans(mixed_expenses):
    card = _card(ExpenseCards.build(mixed_expenses), "Per metus")

    expected = sum(EXPENSES_REGULAR) + sum(EXPENSES_NECESSARY) + sum(NECESSARY)
    assert card.value == _euro(expected)


def test_expense_cards_necessary_is_necessary_expense_plans_and_necessary_plans(
    mixed_expenses,
):
    card = _card(ExpenseCards.build(mixed_expenses), "Būtinos")

    assert card.value == _euro(sum(EXPENSES_NECESSARY) + sum(NECESSARY))


def test_expense_cards_necessary_is_empty_without_necessary_plans():
    data = _data(expenses_regular=[1000] * 12)

    card = _card(ExpenseCards.build(data), "Būtinos")

    assert card.state == EMPTY


@pytest.mark.django_db
def test_expense_cards_read_no_income_saving_or_day_plans(main_user):
    plan = ExpensePlanFactory()
    NecessaryPlanFactory()
    data = PlanCollectData(main_user, plan.year).get_data()

    with CaptureQueriesContext(connection) as queries:
        ExpenseCards.build(data)

    sql = " ".join(query["sql"] for query in queries.captured_queries)
    for table in ("plans_incomeplan", "plans_savingplan", "plans_dayplan"):
        assert table not in sql


def test_expense_cards_a_saving_plan_changes_no_card():
    plans = {
        "expenses_regular": [100_000] * 12,
        "expenses_necessary": [50_000] * 12,
        "necessary": [20_000] * 12,
    }
    savings = [10_000] * 12
    raised_savings = [20_000] + [10_000] * 11

    base = {c.title: c for c in ExpenseCards.build(_data(**plans, savings=savings))}
    raised = {
        c.title: c for c in ExpenseCards.build(_data(**plans, savings=raised_savings))
    }

    assert base["Būtinos"].value == _euro(840_000)
    for title in ("Per metus", "Būtinos", "Kasdienės", "Per mėnesį"):
        assert raised[title].value == base[title].value


def test_expense_cards_no_card_has_an_explanation(mixed_expenses):
    cards = ExpenseCards.build(mixed_expenses)

    assert all(card.explanation == () for card in cards)


def test_expense_cards_everyday_is_expense_plans_of_non_necessary_types(
    mixed_expenses,
):
    card = _card(ExpenseCards.build(mixed_expenses), "Kasdienės")

    assert card.value == _euro(sum(EXPENSES_REGULAR))


def test_expense_cards_per_month_pinned_to_a_literal():
    data = _data(expenses_regular=[1_000_000] + [0] * 11)

    card = _card(ExpenseCards.build(data), "Per mėnesį")

    assert card.value == "833"


def test_expense_cards_are_empty_without_expense_or_necessary_plans_even_with_savings():
    data = _data(
        expenses_regular=ZERO_MONTHS,
        expenses_necessary=ZERO_MONTHS,
        necessary=ZERO_MONTHS,
        savings=[300_000] + [0] * 11,
    )

    cards = ExpenseCards.build(data)

    assert [c.state for c in cards] == [EMPTY, EMPTY, EMPTY, EMPTY]
    assert all("0" not in c.value for c in cards)


def test_expense_cards_everyday_is_empty_without_expense_plans_of_non_necessary_types():
    data = _data(expenses_necessary=[500] * 12, necessary=[200] * 12)

    card = _card(ExpenseCards.build(data), "Kasdienės")

    assert card.state == EMPTY


def test_expense_cards_necessary_and_everyday_add_up_to_the_year():
    expenses_regular = [1000] * 12
    expenses_necessary = [500] * 12
    necessary = [200] * 12
    data = _data(
        expenses_regular=expenses_regular,
        expenses_necessary=expenses_necessary,
        necessary=necessary,
        savings=[100] * 12,
    )

    cards = {c.title: c for c in ExpenseCards.build(data)}

    necessary_cents = sum(expenses_necessary) + sum(necessary)
    everyday_cents = sum(expenses_regular)
    year_cents = necessary_cents + everyday_cents

    assert cards["Būtinos"].value == _euro(necessary_cents)
    assert cards["Kasdienės"].value == _euro(everyday_cents)
    assert cards["Per metus"].value == _euro(year_cents)


# Suma dienai
INCOMES_FOR_25_PER_DAY = [75_000] * 12


def test_day_cards_titles_in_order():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[3000] * 12)

    cards = {card.title: card for card in DayCards.build(data, 6)}

    assert list(cards) == ["Suma dienai šį mėnesį", "Dienos planas šį mėnesį"]


def test_day_cards_read_the_given_month_not_another():
    per_day = [0] * 12
    per_day[5] = 3000
    per_day[0] = 1000
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=per_day)

    card = _card(DayCards.build(data, 6), "Dienos planas šį mėnesį")

    assert card.value == _euro_cents(3000)


def test_day_cards_state_high_when_day_plan_is_above_sum_per_day():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[3000] * 12)

    card = _card(DayCards.build(data, 6), "Dienos planas šį mėnesį")

    assert card.state == HIGH


def test_day_cards_state_neutral_when_day_plan_equals_sum_per_day():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[2500] * 12)

    card = _card(DayCards.build(data, 6), "Dienos planas šį mėnesį")

    assert card.state == NEUTRAL


def test_day_cards_day_plan_is_empty_without_a_day_plan_for_the_month():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=ZERO_MONTHS)

    card = _card(DayCards.build(data, 6), "Dienos planas šį mėnesį")

    assert card.state == EMPTY


def test_day_cards_sum_per_day_is_empty_without_income_plans():
    data = _data(incomes=ZERO_MONTHS, per_day=[3000] * 12)

    card = _card(DayCards.build(data, 6), "Suma dienai šį mėnesį")

    assert card.state == EMPTY


def test_day_cards_sum_per_day_shows_even_when_negative():
    data = _data(
        incomes=[100] * 12, expenses_necessary=[100_000] * 12, per_day=[3000] * 12
    )

    expected = PlanCalculateDaySum(data).day_calced["6"]

    card = _card(DayCards.build(data, 6), "Suma dienai šį mėnesį")

    assert card.state != EMPTY
    assert card.value == _euro_cents(expected)
    assert expected < 0


def test_day_cards_value_formatted_with_two_decimals():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[3000] * 12)

    cards = {c.title: c for c in DayCards.build(data, 6)}

    assert cards["Suma dienai šį mėnesį"].value == "25,00"
    assert cards["Dienos planas šį mėnesį"].value == "30,00"
