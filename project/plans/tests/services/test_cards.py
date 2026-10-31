import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....core.lib.stat_card import EMPTY, HIGH, NEUTRAL
from ...lib.calc_day_sum import DataDto, PlanCalculateDaySum, PlanCollectData
from ...services.cards import DayCards, ExpenseCards, IncomeCards, SavingCards
from ..factories import ExpensePlanFactory, NecessaryPlanFactory

ZERO_MONTHS = [0] * 12
MONTH_LEN = [{"month": m, "amount": 30} for m in range(1, 13)]
INCOMES_FOR_25_PER_DAY = [75_000] * 12


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


def _day_cards(data):
    return DayCards.build(PlanCalculateDaySum(data), 6)


@pytest.mark.parametrize(
    "build, data, titles",
    [
        pytest.param(
            IncomeCards.build,
            _data(incomes=[1000] * 12),
            ["Per metus", "Mėnesio mediana"],
            id="incomes",
        ),
        pytest.param(
            SavingCards.build,
            _data(incomes=[100_000] * 12, savings=[25_000] * 12),
            ["Per metus", "Planuotų pajamų dalis", "Per mėnesį"],
            id="savings",
        ),
        pytest.param(
            ExpenseCards.build,
            _data(expenses_regular=[1000] * 12, necessary=[200] * 12),
            ["Per metus", "Būtinos", "Kasdienės", "Per mėnesį"],
            id="expenses",
        ),
        pytest.param(
            _day_cards,
            _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[3000] * 12),
            ["Suma dienai šį mėnesį", "Dienos planas šį mėnesį"],
            id="day",
        ),
    ],
)
def test_cards_titles_in_order(build, data, titles):
    assert [card.title for card in build(data)] == titles


@pytest.mark.parametrize(
    "build, data, empty",
    [
        pytest.param(
            IncomeCards.build,
            _data(),
            ["Per metus", "Mėnesio mediana"],
            id="incomes",
        ),
        pytest.param(
            SavingCards.build,
            _data(incomes=[1_200_000] * 12),
            ["Per metus", "Planuotų pajamų dalis", "Per mėnesį"],
            id="savings-with-incomes",
        ),
        pytest.param(
            ExpenseCards.build,
            _data(savings=[300_000] + [0] * 11),
            ["Per metus", "Būtinos", "Kasdienės", "Per mėnesį"],
            id="expenses-with-savings",
        ),
        pytest.param(
            ExpenseCards.build,
            _data(expenses_regular=[1000] * 12),
            ["Būtinos"],
            id="necessary",
        ),
        pytest.param(
            ExpenseCards.build,
            _data(expenses_necessary=[500] * 12, necessary=[200] * 12),
            ["Kasdienės"],
            id="everyday",
        ),
    ],
)
def test_cards_are_empty_without_their_plans(build, data, empty):
    cards = build(data)

    assert [card.title for card in cards if card.state == EMPTY] == empty


@pytest.mark.parametrize(
    "build, data",
    [
        pytest.param(
            SavingCards.build,
            _data(incomes=[1_200_000] * 12, savings=[1_000_000] + [0] * 11),
            id="savings",
        ),
        pytest.param(
            ExpenseCards.build,
            _data(expenses_regular=[1_000_000] + [0] * 11),
            id="expenses",
        ),
    ],
)
def test_cards_per_month_divides_the_year_total_by_twelve(build, data):
    card = _card(build(data), "Per mėnesį")

    assert card.value == "833"


# Pajamos
def test_income_cards_per_year_is_the_year_total():
    data = _data(incomes=[1000] * 12)

    card = _card(IncomeCards.build(data), "Per metus")

    assert card.value == "120"


def test_income_cards_median_is_the_monthly_median():
    # the mean is 9250 cents, the median 1000
    data = _data(incomes=[1000] * 11 + [100_000])

    card = _card(IncomeCards.build(data), "Mėnesio mediana")

    assert card.value == "10"


# Taupymas
def test_saving_cards_per_year_is_the_year_total():
    data = _data(incomes=[100_000] * 12, savings=[25_000] * 12)

    card = _card(SavingCards.build(data), "Per metus")

    assert card.value == "3.000"


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


# Išlaidos
@pytest.fixture
def mixed_expenses():
    return _data(
        expenses_regular=[1000] * 12,
        expenses_necessary=[500] * 12,
        necessary=[200] * 12,
        savings=[100] * 12,
    )


@pytest.mark.parametrize(
    "title, value",
    [
        pytest.param("Per metus", "204", id="year-is-expense-and-necessary-plans"),
        pytest.param("Būtinos", "84", id="necessary-is-necessary-plans"),
        pytest.param("Kasdienės", "120", id="everyday-is-non-necessary-types"),
    ],
)
def test_expense_cards_sum_their_plans(mixed_expenses, title, value):
    card = _card(ExpenseCards.build(mixed_expenses), title)

    assert card.value == value


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

    assert base["Būtinos"].value == "8.400"
    for title in ("Per metus", "Būtinos", "Kasdienės", "Per mėnesį"):
        assert raised[title].value == base[title].value


def test_expense_cards_no_card_has_an_explanation(mixed_expenses):
    cards = ExpenseCards.build(mixed_expenses)

    assert all(card.explanation == () for card in cards)


# Suma dienai
def test_day_cards_read_the_given_month_not_another():
    per_day = [0] * 12
    per_day[5] = 3000
    per_day[0] = 1000
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=per_day)

    card = _card(_day_cards(data), "Dienos planas šį mėnesį")

    assert card.value == "30,00"


@pytest.mark.parametrize(
    "per_day, state",
    [
        pytest.param(3000, HIGH, id="above"),
        pytest.param(2500, NEUTRAL, id="equal"),
    ],
)
def test_day_cards_day_plan_state_against_sum_per_day(per_day, state):
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[per_day] * 12)

    card = _card(_day_cards(data), "Dienos planas šį mėnesį")

    assert card.state == state


def test_day_cards_day_plan_is_empty_without_a_day_plan_for_the_month():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=ZERO_MONTHS)

    card = _card(_day_cards(data), "Dienos planas šį mėnesį")

    assert card.state == EMPTY


def test_day_cards_sum_per_day_is_empty_without_income_plans():
    data = _data(incomes=ZERO_MONTHS, per_day=[3000] * 12)

    card = _card(_day_cards(data), "Suma dienai šį mėnesį")

    assert card.state == EMPTY


def test_day_cards_sum_per_day_shows_even_when_negative():
    # (100 − 100 000) ÷ 30 days = −3330 cents
    data = _data(
        incomes=[100] * 12, expenses_necessary=[100_000] * 12, per_day=[3000] * 12
    )

    card = _card(_day_cards(data), "Suma dienai šį mėnesį")

    assert card.value == "-33,30"


def test_day_cards_sum_per_day_has_two_decimals():
    data = _data(incomes=INCOMES_FOR_25_PER_DAY, per_day=[3000] * 12)

    card = _card(_day_cards(data), "Suma dienai šį mėnesį")

    assert card.value == "25,00"
