import pytest

from ...users.factories import UserFactory
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


def test_income_related(get_user):
    IncomePlanFactory()
    IncomePlanFactory(user=UserFactory(username='XXX'))

    actual = IncomePlan.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_income_year(get_user):
    IncomePlanFactory()
    IncomePlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = list(IncomePlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_income_items(get_user):
    t1 = IncomeTypeFactory(title='T1')
    t2 = IncomeTypeFactory(title='T2')

    IncomePlanFactory(income_type=t1)
    IncomePlanFactory(income_type=t2)

    IncomePlanFactory(user=UserFactory(username='XXX'))

    actual = IncomePlan.objects.items()

    assert len(actual) == 2
    assert str(actual[0].income_type) == 'T1'
    assert actual[0].user.username == 'bob'
    assert str(actual[1].income_type) == 'T2'
    assert actual[1].user.username == 'bob'


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


def test_expense_related(get_user):
    ExpensePlanFactory()
    ExpensePlanFactory(user=UserFactory(username='XXX'))

    actual = ExpensePlan.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_expense_year(get_user):
    ExpensePlanFactory()
    ExpensePlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = list(ExpensePlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_expense_items(get_user):
    t1 = ExpenseTypeFactory(title='T1')
    t2 = ExpenseTypeFactory(title='T2')

    ExpensePlanFactory(expense_type=t1)
    ExpensePlanFactory(expense_type=t2)

    ExpensePlanFactory(user=UserFactory(username='XXX'))

    actual = ExpensePlan.objects.items()

    assert len(actual) == 2
    assert str(actual[0].expense_type) == 'T1'
    assert actual[0].user.username == 'bob'
    assert str(actual[1].expense_type) == 'T2'
    assert actual[1].user.username == 'bob'


@pytest.mark.xfail
def test_expense_no_dublicates():
    type_ = ExpenseTypeFactory(title='X')
    ExpensePlan(year=2000, expense_type=type_).save()
    ExpensePlan(year=2000, expense_type=type_).save()



def test_expense_year_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlan.objects.year(1999))


def test_expense_items_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlan.objects.items())



# ----------------------------------------------------------------------------
#                                                                  Saving Plan
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingPlanFactory.build(year=2000)

    assert str(actual) == '2000/Savings'


def test_saving_related(get_user):
    SavingPlanFactory()
    SavingPlanFactory(user=UserFactory(username='XXX'))

    actual = SavingPlan.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_saving_year(get_user):
    SavingPlanFactory()
    SavingPlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = list(SavingPlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_saving_items(get_user):
    t1 = SavingTypeFactory(title='T1')
    t2 = SavingTypeFactory(title='T2')

    SavingPlanFactory(saving_type=t1)
    SavingPlanFactory(saving_type=t2)

    SavingPlanFactory(user=UserFactory(username='XXX'))

    actual = SavingPlan.objects.items()

    assert len(actual) == 2
    assert str(actual[0].saving_type) == 'T1'
    assert actual[0].user.username == 'bob'
    assert str(actual[1].saving_type) == 'T2'
    assert actual[1].user.username == 'bob'


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


def test_day_related(get_user):
    DayPlanFactory()
    DayPlanFactory(user=UserFactory(username='XXX'))

    actual = DayPlan.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_day_year(get_user):
    DayPlanFactory()
    DayPlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = list(DayPlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_day_items(get_user):
    DayPlanFactory()
    DayPlanFactory(year=1974)
    DayPlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = DayPlan.objects.items()

    assert len(actual) == 2
    assert actual[0].user.username == 'bob'
    assert actual[0].year == 1974
    assert actual[1].user.username == 'bob'
    assert actual[1].year == 1999


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


def test_necessary_related(get_user):
    NecessaryPlanFactory()
    NecessaryPlanFactory(user=UserFactory(username='XXX'))

    actual = NecessaryPlan.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_necessary_year(get_user):
    NecessaryPlanFactory()
    NecessaryPlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = list(NecessaryPlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_necessary_items(get_user):
    NecessaryPlanFactory()
    NecessaryPlanFactory(year=1974)
    NecessaryPlanFactory(year=1974, user=UserFactory(username='XXX'))

    actual = NecessaryPlan.objects.items()

    assert len(actual) == 2
    assert actual[0].user.username == 'bob'
    assert actual[0].year == 1974
    assert actual[0].title == 'other'
    assert actual[1].user.username == 'bob'
    assert actual[1].year == 1999
    assert actual[1].title == 'other'


@pytest.mark.xfail(raises=Exception)
def test_necessary_no_dublicates():
    NecessaryPlanFactory(year=2000, title='N')
    NecessaryPlanFactory(year=2000, title='N')
