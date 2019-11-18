import pytest

from ...auths.factories import UserFactory
from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from ..factories import (
    DayPlanFactory, ExpensePlanFactory, IncomePlanFactory,
    NecessaryPlanFactory, SavingPlanFactory)
from ..models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                      SavingPlan)

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Income Plan
# ----------------------------------------------------------------------------
def test_income_str():
    actual = IncomePlanFactory.build(year=2000)

    assert str(actual) == '2000/Income Type'


@pytest.mark.xfail
def test_income_no_dublicates():
    type_ = IncomeTypeFactory(title='X')
    IncomePlan(year=2000, income_type=type_).save()
    IncomePlan(year=2000, income_type=type_).save()


# ----------------------------------------------------------------------------
#                                                                 Expense Plan
# ----------------------------------------------------------------------------
def test_expense_str():
    actual = ExpensePlanFactory.build(year=2000)

    assert str(actual) == '2000/Expense Type'


@pytest.mark.xfail
def test_expense_no_dublicates():
    type_ = ExpenseTypeFactory(title='X')
    ExpensePlan(year=2000, expense_type=type_).save()
    ExpensePlan(year=2000, expense_type=type_).save()


def test_expense_year():
    ExpensePlanFactory(year=1999)
    ExpensePlanFactory(year=2010)

    actual = ExpensePlan.objects.year(2010)

    assert actual.count() == 1


def test_expense_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlan.objects.year(1999))


def test_expense_items():
    ExpensePlanFactory(year=1999)
    ExpensePlanFactory(year=2010)

    actual = ExpensePlan.objects.items()

    assert actual.count() == 1


def test_expense_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlan.objects.items())



# ----------------------------------------------------------------------------
#                                                                  Saving Plan
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingPlanFactory.build(year=2000)

    assert str(actual) == '2000/Savings'


@pytest.mark.xfail
def test_saving_no_dublicates():
    type_ = SavingTypeFactory(title='X')
    SavingPlan(year=2000, saving_type=type_).save()
    SavingPlan(year=2000, saving_type=type_).save()


# ----------------------------------------------------------------------------
#                                                                     Day Plan
# ----------------------------------------------------------------------------
def test_day_str():
    actual = DayPlanFactory.build(year=2000)

    assert str(actual) == '2000'


@pytest.mark.xfail(raises=Exception)
def test_day_no_dublicates():
    DayPlanFactory(year=2000)
    DayPlanFactory(year=2000)


# ----------------------------------------------------------------------------
#                                                               Necessary Plan
# ----------------------------------------------------------------------------
def test_necessary_str():
    actual = NecessaryPlanFactory.build(year=2000, title='N')

    assert str(actual) == '2000/N'


@pytest.mark.xfail(raises=Exception)
def test_necessary_no_dublicates():
    NecessaryPlanFactory(year=2000, title='N')
    NecessaryPlanFactory(year=2000, title='N')
