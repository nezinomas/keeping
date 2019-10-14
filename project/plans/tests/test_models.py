import pytest

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...savings.factories import SavingTypeFactory
from .. import factories, models


def test_necessary_str():
    actual = factories.NecessaryPlanFactory.build(year=2000, title='N')

    assert '2000/N' == str(actual)


@pytest.mark.django_db
@pytest.mark.xfail(raises=Exception)
def test_necessary_no_dublicates():
    factories.NecessaryPlanFactory(year=2000, title='N')
    factories.NecessaryPlanFactory(year=2000, title='N')


def test_day_str():
    actual = factories.DayPlanFactory.build(year=2000)

    assert '2000' == str(actual)


@pytest.mark.django_db
@pytest.mark.xfail(raises=Exception)
def test_day_no_dublicates():
    factories.DayPlanFactory(year=2000)
    factories.DayPlanFactory(year=2000)


def test_income_str():
    actual = factories.IncomePlanFactory.build(year=2000)

    assert '2000/Income Type' == str(actual)


@pytest.mark.django_db
@pytest.mark.xfail
def test_income_no_dublicates():
    type_ = IncomeTypeFactory(title='X')
    models.IncomePlan(year=2000, income_type=type_).save()
    models.IncomePlan(year=2000, income_type=type_).save()


def test_expense_str():
    actual = factories.ExpensePlanFactory.build(year=2000)

    assert '2000/Expense Type' == str(actual)


@pytest.mark.django_db
@pytest.mark.xfail
def test_expense_no_dublicates():
    type_ = ExpenseTypeFactory(title='X')
    models.ExpensePlan(year=2000, expense_type=type_).save()
    models.ExpensePlan(year=2000, expense_type=type_).save()


def test_saving_str():
    actual = factories.SavingPlanFactory.build(year=2000)

    assert '2000/Savings' == str(actual)


@pytest.mark.django_db
@pytest.mark.xfail
def test_saving_no_dublicates():
    type_ = SavingTypeFactory(title='X')
    models.SavingPlan(year=2000, saving_type=type_).save()
    models.SavingPlan(year=2000, saving_type=type_).save()


@pytest.mark.django_db
def expense_plan_year():
    factories.ExpensePlanFactory(year=1999)
    factories.ExpensePlanFactory(year=2010)

    actual = models.ExpensePlan.objects.year(2010)

    assert 1 == actual.count()


@pytest.mark.django_db
def test_expense_plan_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*models.ExpensePlan.objects.year(1999)]


@pytest.mark.django_db
def expense_plan_items():
    factories.ExpensePlanFactory(year=1999)
    factories.ExpensePlanFactory(year=2010)

    actual = models.ExpensePlan.objects.items()

    assert 1 == actual.count()


@pytest.mark.django_db
def test_expense_plan_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*models.ExpensePlan.objects.items()]
