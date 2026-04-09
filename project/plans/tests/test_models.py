import pytest
from django.db.models.signals import post_save
from django.utils.translation import gettext as _
from factory.django import mute_signals

from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...savings.tests.factories import SavingTypeFactory
from ..models import ExpensePlan, IncomePlan, SavingPlan
from ..services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    PlanAggregatorService,
    SavingPlanModelService,
)
from .factories import (
    DayPlanFactory,
    ExpensePlanFactory,
    IncomePlanFactory,
    NecessaryPlanFactory,
    SavingPlanFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def mute_my_signals():
    with mute_signals(post_save):
        yield


# ----------------------------------------------------------------------------
#                                                                Common method
# ----------------------------------------------------------------------------
def test_targets_fills_zeros_for_empty_plans(main_user):
    ExpenseTypeFactory(title="T1")
    ExpenseTypeFactory(title="T2")

    actual = PlanAggregatorService(main_user).get_monthly_plan_targets(1999, month=2)

    expect = {"T1": 0, "T2": 0, _("Savings"): 0}

    assert actual == expect


def test_targets_sums_correctly_and_ignores_other_months(main_user):
    # Setup: Create 3 distinct expense types
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")
    t3 = ExpenseTypeFactory(title="T3")

    ExpensePlanFactory(month=2, expense_type=t1, price=100)
    NecessaryPlanFactory(month=2, expense_type=t1, price=50)
    NecessaryPlanFactory(month=2, expense_type=t2, price=200)
    SavingPlanFactory(month=2, price=300)

    ExpensePlanFactory(month=3, expense_type=t3, price=999)
    SavingPlanFactory(month=3, price=999)

    actual = PlanAggregatorService(main_user).get_monthly_plan_targets(1999, month=2)

    expect = {"T1": 150, "T2": 200, "T3": 0, _("Savings"): 300}

    assert actual == expect


def test_targets_no_savings(main_user):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")
    t3 = ExpenseTypeFactory(title="T3")

    ExpensePlanFactory(month=2, expense_type=t1, price=100)
    NecessaryPlanFactory(month=2, expense_type=t1, price=50)
    NecessaryPlanFactory(month=2, expense_type=t2, price=200)
    ExpensePlanFactory(month=3, expense_type=t3, price=999)

    actual = PlanAggregatorService(main_user).get_monthly_plan_targets(1999, month=2)

    expect = {"T1": 150, "T2": 200, "T3": 0, _("Savings"): 0}

    assert actual == expect


# ----------------------------------------------------------------------------
#                                                                  Income Plan
# ----------------------------------------------------------------------------
def test_income_str():
    actual = IncomePlanFactory.build(year=2000)

    assert str(actual) == "2000/Income Type"


def test_income_related(main_user, second_user):
    IncomePlanFactory()
    IncomePlanFactory(journal=second_user.journal)

    actual = IncomePlanModelService(main_user).items()

    assert len(actual) == 1
    assert actual[0].journal.users.first().username == "bob"


def test_income_year(main_user, second_user):
    IncomePlanFactory(year=1999, month=1, price=1)
    IncomePlanFactory(year=1999, month=2, price=2)
    IncomePlanFactory(year=1974, journal=second_user.journal)

    actual = list(IncomePlanModelService(main_user).year(1999))

    assert len(actual) == 2
    assert actual[0].year == 1999
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].month == 1
    assert actual[0].price == 1

    assert actual[1].year == 1999
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].month == 2
    assert actual[1].price == 2


def test_income_summed_by_month(main_user, second_user):
    t1 = IncomeTypeFactory(title="AAA")
    t2 = IncomeTypeFactory(title="ZZZ")

    IncomePlanFactory(year=1999, month=1, price=1, income_type=t1)
    IncomePlanFactory(year=1999, month=2, price=2, income_type=t1)
    IncomePlanFactory(year=1999, month=2, price=2, income_type=t2)
    IncomePlanFactory(year=1974, journal=second_user.journal)

    actual = list(IncomePlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


def test_income_items(main_user, second_user):
    t1 = IncomeTypeFactory(title="T1")
    t2 = IncomeTypeFactory(title="T2")

    IncomePlanFactory(income_type=t1)
    IncomePlanFactory(income_type=t2)

    IncomePlanFactory(journal=second_user.journal)

    actual = IncomePlanModelService(main_user).items()

    assert len(actual) == 2
    assert str(actual[0].income_type) == "T1"
    assert actual[0].journal.users.first().username == "bob"
    assert str(actual[1].income_type) == "T2"
    assert actual[1].journal.users.first().username == "bob"


def test_income_pivot_table(main_user):
    salary = IncomeTypeFactory(title="Salary")
    bonus = IncomeTypeFactory(title="Bonus")

    IncomePlanFactory(month=1, price=1, income_type=salary)
    IncomePlanFactory(month=2, price=2, income_type=salary)
    IncomePlanFactory(month=12, price=5, income_type=bonus)
    IncomePlanFactory(year=2027, month=1, price=9, income_type=salary)

    actual = IncomePlanModelService(main_user).pivot_table(year=1999)

    assert actual == {bonus: {12: 5}, salary: {1: 1, 2: 2}}


def test_income_pivot_table_no_data(main_user):
    actual = IncomePlanModelService(main_user).pivot_table(year=1999)

    assert actual == {}


@pytest.mark.xfail
def test_income_no_dublicates():
    type_ = IncomeTypeFactory(title="X")
    IncomePlan(year=2000, month=1, income_type=type_).save()
    IncomePlan(year=2000, month=1, income_type=type_).save()


# ----------------------------------------------------------------------------
#                                                                 Expense Plan
# ----------------------------------------------------------------------------
def test_expense_str():
    actual = ExpensePlanFactory.build(year=2000)

    assert str(actual) == "2000/Expense Type"


def test_expense_objects(main_user, second_user):
    ExpensePlanFactory()
    ExpensePlanFactory(journal=second_user.journal)

    actual = ExpensePlanModelService(main_user).objects

    assert len(actual) == 1
    assert actual[0].journal.users.first().username == "bob"


def test_expense_year(main_user, second_user):
    ExpensePlanFactory(year=1999, month=1, price=1)
    ExpensePlanFactory(year=1999, month=2, price=2)
    ExpensePlanFactory(year=1974, journal=second_user.journal)

    actual = list(ExpensePlanModelService(main_user).year(1999))

    assert len(actual) == 2
    assert actual[0].year == 1999
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].month == 1
    assert actual[0].price == 1

    assert actual[1].year == 1999
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].month == 2
    assert actual[1].price == 2


def test_expense_summed_by_month_expenses_regular(main_user, second_user):
    t1 = ExpenseTypeFactory(title="AAA")
    t2 = ExpenseTypeFactory(title="ZZZ")
    t3 = ExpenseTypeFactory(title="XXX", necessary=True)

    ExpensePlanFactory(year=1999, month=1, price=1, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t2)
    ExpensePlanFactory(year=1999, month=2, price=4, expense_type=t3)
    ExpensePlanFactory(year=1974, journal=second_user.journal)

    actual = list(ExpensePlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


def test_expense_summed_by_month_expenses_necessary(main_user, second_user):
    t1 = ExpenseTypeFactory(title="AAA", necessary=True)
    t2 = ExpenseTypeFactory(title="ZZZ", necessary=True)
    t3 = ExpenseTypeFactory(title="XXX")

    ExpensePlanFactory(year=1999, month=1, price=1, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t1)
    ExpensePlanFactory(year=1999, month=2, price=2, expense_type=t2)
    ExpensePlanFactory(year=1999, month=2, price=4, expense_type=t3)
    ExpensePlanFactory(year=1974, journal=second_user.journal)

    actual = list(
        ExpensePlanModelService(main_user).summed_by_month(1999, necessary=True)
    )

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


def test_expense_items(main_user, second_user):
    t1 = ExpenseTypeFactory(title="T1")
    t2 = ExpenseTypeFactory(title="T2")

    ExpensePlanFactory(expense_type=t1)
    ExpensePlanFactory(expense_type=t2)

    ExpensePlanFactory(journal=second_user.journal)

    actual = ExpensePlanModelService(main_user).items()

    assert len(actual) == 2
    assert str(actual[0].expense_type) == "T1"
    assert actual[0].journal.users.first().username == "bob"
    assert str(actual[1].expense_type) == "T2"
    assert actual[1].journal.users.first().username == "bob"


@pytest.mark.xfail
def test_expense_no_dublicates():
    type_ = ExpenseTypeFactory(title="X")
    ExpensePlan(year=2000, month=1, expense_type=type_).save()
    ExpensePlan(year=2000, month=1, expense_type=type_).save()


def test_expense_year_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlanModelService(main_user).year(1999))


def test_expense_pivot_table(main_user):
    e1 = ExpenseTypeFactory(title="ZZZ")
    e2 = ExpenseTypeFactory(title="AAA")

    ExpensePlanFactory(month=1, price=1, expense_type=e1)
    ExpensePlanFactory(month=2, price=2, expense_type=e1)
    ExpensePlanFactory(month=12, price=5, expense_type=e2)
    ExpensePlanFactory(year=2027, month=1, price=9, expense_type=e1)

    actual = ExpensePlanModelService(main_user).pivot_table(year=1999)

    assert actual == {e2: {12: 5}, e1: {1: 1, 2: 2}}


def test_expense_items_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlanModelService(main_user).items())


# ----------------------------------------------------------------------------
#                                                                  Saving Plan
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingPlanFactory.build(year=2000)

    assert str(actual) == "2000/Savings"


def test_saving_objects(main_user, second_user):
    SavingPlanFactory()
    SavingPlanFactory(journal=second_user.journal)

    actual = SavingPlanModelService(main_user).objects

    assert len(actual) == 1
    assert actual[0].journal.users.first().username == "bob"


def test_saving_year(main_user, second_user):
    SavingPlanFactory(year=1999, month=1, price=1)
    SavingPlanFactory(year=1999, month=2, price=2)
    SavingPlanFactory(year=1974, journal=second_user.journal)

    actual = list(SavingPlanModelService(main_user).year(1999))

    assert len(actual) == 2
    assert actual[0].year == 1999
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].month == 1
    assert actual[0].price == 1

    assert actual[1].year == 1999
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].month == 2
    assert actual[1].price == 2


def test_saving_summed_by_month(main_user, second_user):
    t1 = SavingTypeFactory(title="AAA")
    t2 = SavingTypeFactory(title="ZZZ")

    SavingPlanFactory(year=1999, month=1, price=1, saving_type=t1)
    SavingPlanFactory(year=1999, month=2, price=2, saving_type=t1)
    SavingPlanFactory(year=1999, month=2, price=2, saving_type=t2)
    SavingPlanFactory(year=1974, journal=second_user.journal)

    actual = list(SavingPlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 1, "amount": 1}, {"month": 2, "amount": 4}]


def test_saving_items(main_user, second_user):
    t1 = SavingTypeFactory(title="T1")
    t2 = SavingTypeFactory(title="T2")

    SavingPlanFactory(saving_type=t1)
    SavingPlanFactory(saving_type=t2)

    SavingPlanFactory(journal=second_user.journal)

    actual = SavingPlanModelService(main_user).items()

    assert len(actual) == 2
    assert str(actual[0].saving_type) == "T1"
    assert actual[0].journal.users.first().username == "bob"
    assert str(actual[1].saving_type) == "T2"
    assert actual[1].journal.users.first().username == "bob"


@pytest.mark.xfail
def test_saving_no_dublicates():
    type_ = SavingTypeFactory(title="X")
    SavingPlan(year=2000, month=1, saving_type=type_).save()
    SavingPlan(year=2000, month=1, saving_type=type_).save()


def test_saving_pivot_table(main_user):
    s1 = SavingTypeFactory(title="ZZZ")
    s2 = SavingTypeFactory(title="AAA")

    SavingPlanFactory(month=1, price=1, saving_type=s1)
    SavingPlanFactory(month=2, price=2, saving_type=s1)
    SavingPlanFactory(month=12, price=5, saving_type=s2)
    SavingPlanFactory(year=2027, month=1, price=9, saving_type=s1)

    actual = SavingPlanModelService(main_user).pivot_table(year=1999)

    assert actual == {s2: {12: 5}, s1: {1: 1, 2: 2}}


# ----------------------------------------------------------------------------
#                                                                     Day Plan
# ----------------------------------------------------------------------------
def test_day_str():
    actual = DayPlanFactory.build(year=2000)

    assert str(actual) == "2000"


def test_day_objects(main_user, second_user):
    DayPlanFactory()
    DayPlanFactory(journal=second_user.journal)

    actual = DayPlanModelService(main_user).objects

    assert len(actual) == 1
    assert actual[0].journal.users.first().username == "bob"


def test_day_year(main_user, second_user):
    DayPlanFactory(year=1999, month=1, price=1)
    DayPlanFactory(year=1999, month=2, price=2)
    DayPlanFactory(year=1974, journal=second_user.journal)

    actual = list(DayPlanModelService(main_user).year(1999))

    assert len(actual) == 2
    assert actual[0].year == 1999
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].month == 1
    assert actual[0].price == 1

    assert actual[1].year == 1999
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].month == 2
    assert actual[1].price == 2


def test_day_summed_by_month(main_user):
    DayPlanFactory(month=2, price=22)

    actual = list(DayPlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 2, "amount": 22}]


def test_day_items(main_user, second_user):
    DayPlanFactory()
    DayPlanFactory(year=1974)
    DayPlanFactory(year=1974, journal=second_user.journal)

    actual = DayPlanModelService(main_user).items()

    assert len(actual) == 2
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].year == 1974
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].year == 1999


def test_day_pivot_table(main_user):
    DayPlanFactory(month=2, price=22)
    DayPlanFactory(month=12, price=222)

    actual = DayPlanModelService(main_user).pivot_table(1999)

    assert actual == {2: 22, 12: 222}


def test_day_pivot_table_no_data(main_user):
    actual = DayPlanModelService(main_user).pivot_table(1999)

    assert actual == {}


@pytest.mark.xfail(raises=Exception)
def test_day_no_dublicates(main_user):
    DayPlanFactory(year=2000, month=1, journal=main_user.journal)
    DayPlanFactory(year=2000, month=1, journal=main_user.journal)


# ----------------------------------------------------------------------------
#                                                               Necessary Plan
# ----------------------------------------------------------------------------
def test_necessary_str():
    actual = NecessaryPlanFactory.build(year=2000, title="N")

    assert str(actual) == "2000/N"


def test_necessary_objects(main_user, second_user):
    NecessaryPlanFactory()
    NecessaryPlanFactory(journal=second_user.journal)

    actual = NecessaryPlanModelService(main_user).objects

    assert len(actual) == 1
    assert actual[0].journal.users.first().username == "bob"


def test_necessary_year(main_user, second_user):
    NecessaryPlanFactory(year=1999, month=1, price=1)
    NecessaryPlanFactory(year=1999, month=2, price=2)
    NecessaryPlanFactory(year=1974, journal=second_user.journal)

    actual = list(NecessaryPlanModelService(main_user).year(1999))

    assert len(actual) == 2
    assert actual[0].year == 1999
    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].month == 1
    assert actual[0].price == 1

    assert actual[1].year == 1999
    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].month == 2
    assert actual[1].price == 2


def test_necessary_summed_by_month(main_user):
    t1 = ExpenseTypeFactory(title="AAA")
    t2 = ExpenseTypeFactory(title="XXX")
    NecessaryPlanFactory(expense_type=t1, title="A", month=2, price=123)
    NecessaryPlanFactory(expense_type=t2, title="A", month=2, price=321)

    actual = list(NecessaryPlanModelService(main_user).summed_by_month(1999))

    assert actual == [{"month": 2, "amount": 444}]


def test_necessary_summed_by_month_no_data(main_user):
    actual = list(NecessaryPlanModelService(main_user).summed_by_month(1999))

    assert not actual


def test_necessary_items(main_user, second_user):
    NecessaryPlanFactory()
    NecessaryPlanFactory(year=1974)
    NecessaryPlanFactory(year=1974, journal=second_user.journal)

    actual = NecessaryPlanModelService(main_user).items()

    assert len(actual) == 2

    assert actual[0].journal.users.first().username == "bob"
    assert actual[0].year == 1974
    assert actual[0].title == "other"

    assert actual[1].journal.users.first().username == "bob"
    assert actual[1].year == 1999
    assert actual[1].title == "other"


@pytest.mark.xfail(raises=Exception)
def test_necessary_no_dublicates(main_user):
    NecessaryPlanFactory(year=2000, month=1, title="N", journal=main_user.journal)
    NecessaryPlanFactory(year=2000, month=1, title="N", journal=main_user.journal)


def test_necessary_same_title(main_user):
    NecessaryPlanFactory(
        year=2000, title="A", expense_type=ExpenseTypeFactory(title="X")
    )
    NecessaryPlanFactory(
        year=2000, title="A", expense_type=ExpenseTypeFactory(title="Y")
    )

    actual = NecessaryPlanModelService(main_user).items()

    assert len(actual) == 2

    assert actual[0].title == "A"
    assert actual[0].expense_type.title == "X"

    assert actual[1].title == "A"
    assert actual[1].expense_type.title == "Y"


def test_necessary_pivot_table(main_user):
    car = ExpenseTypeFactory(title="Car")
    NecessaryPlanFactory(expense_type=car, title="Insurance", month=2, price=123)

    actual = NecessaryPlanModelService(main_user).pivot_table(1999)

    assert actual == {(car, "Insurance"): {2: 123}}


def test_necessary_pivot_table_no_data(main_user):
    actual = NecessaryPlanModelService(main_user).pivot_table(1999)

    assert actual == {}
