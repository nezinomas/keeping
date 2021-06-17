import pytest

from ...expenses.factories import ExpenseTypeFactory
from ...incomes.factories import IncomeTypeFactory
from ...journals.factories import JournalFactory
from ...savings.factories import SavingTypeFactory
from ...users.factories import UserFactory
from ..factories import (DayPlanFactory, ExpensePlanFactory, IncomePlanFactory,
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


def test_income_related():
    j = JournalFactory(user=UserFactory(username='X'))
    IncomePlanFactory()
    IncomePlanFactory(journal=j)

    actual = IncomePlan.objects.related()

    assert len(actual) == 1
    assert actual[0].journal.user.username == 'bob'


def test_income_year():
    j = JournalFactory(user=UserFactory(username='X'))
    IncomePlanFactory()
    IncomePlanFactory(year=1974, journal=j)

    actual = list(IncomePlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].journal.user.username == 'bob'


def test_income_items():
    t1 = IncomeTypeFactory(title='T1')
    t2 = IncomeTypeFactory(title='T2')

    IncomePlanFactory(income_type=t1)
    IncomePlanFactory(income_type=t2)

    j = JournalFactory(user=UserFactory(username='X'))
    IncomePlanFactory(journal=j)

    actual = IncomePlan.objects.items()

    assert len(actual) == 2
    assert str(actual[0].income_type) == 'T1'
    assert actual[0].journal.user.username == 'bob'
    assert str(actual[1].income_type) == 'T2'
    assert actual[1].journal.user.username == 'bob'


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


def test_expense_related():
    j = JournalFactory(user=UserFactory(username='X'))
    ExpensePlanFactory()
    ExpensePlanFactory(journal=j)

    actual = ExpensePlan.objects.related()

    assert len(actual) == 1
    assert actual[0].journal.user.username == 'bob'


def test_expense_year():
    j = JournalFactory(user=UserFactory(username='X'))
    ExpensePlanFactory()
    ExpensePlanFactory(year=1974, journal=j)

    actual = list(ExpensePlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].journal.user.username == 'bob'


def test_expense_items():
    t1 = ExpenseTypeFactory(title='T1')
    t2 = ExpenseTypeFactory(title='T2')

    ExpensePlanFactory(expense_type=t1)
    ExpensePlanFactory(expense_type=t2)

    ExpensePlanFactory(journal=JournalFactory(user=UserFactory(username='X')))

    actual = ExpensePlan.objects.items()

    assert len(actual) == 2
    assert str(actual[0].expense_type) == 'T1'
    assert actual[0].journal.user.username == 'bob'
    assert str(actual[1].expense_type) == 'T2'
    assert actual[1].journal.user.username == 'bob'


@pytest.mark.xfail
def test_expense_no_dublicates():
    type_ = ExpenseTypeFactory(title='X')
    ExpensePlan(year=2000, expense_type=type_).save()
    ExpensePlan(year=2000, expense_type=type_).save()



def test_expense_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlan.objects.year(1999))


def test_expense_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(ExpensePlan.objects.items())


# ----------------------------------------------------------------------------
#                                                                  Saving Plan
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingPlanFactory.build(year=2000)

    assert str(actual) == '2000/Savings'


def test_saving_related():
    j = JournalFactory(user=UserFactory(username='X'))
    SavingPlanFactory()
    SavingPlanFactory(journal=j)

    actual = SavingPlan.objects.related()

    assert len(actual) == 1
    assert actual[0].journal.user.username == 'bob'


def test_saving_year():
    j = JournalFactory(user=UserFactory(username='X'))
    SavingPlanFactory()
    SavingPlanFactory(year=1974, journal=j)

    actual = list(SavingPlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].journal.user.username == 'bob'


def test_saving_items():
    t1 = SavingTypeFactory(title='T1')
    t2 = SavingTypeFactory(title='T2')

    SavingPlanFactory(saving_type=t1)
    SavingPlanFactory(saving_type=t2)

    SavingPlanFactory(journal=JournalFactory(user=UserFactory(username='X')))

    actual = SavingPlan.objects.items()

    assert len(actual) == 2
    assert str(actual[0].saving_type) == 'T1'
    assert actual[0].journal.user.username == 'bob'
    assert str(actual[1].saving_type) == 'T2'
    assert actual[1].journal.user.username == 'bob'


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


def test_day_related():
    j = JournalFactory(user=UserFactory(username='X'))
    DayPlanFactory()
    DayPlanFactory(journal=j)

    actual = DayPlan.objects.related()

    assert len(actual) == 1
    assert actual[0].journal.user.username == 'bob'


def test_day_year():
    DayPlanFactory()
    DayPlanFactory(year=1974, journal=JournalFactory(user=UserFactory(username='X')))

    actual = list(DayPlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].journal.user.username == 'bob'


def test_day_items():
    j = JournalFactory(user=UserFactory(username='X'))
    DayPlanFactory()
    DayPlanFactory(year=1974)
    DayPlanFactory(year=1974, journal=j)

    actual = DayPlan.objects.items()

    assert len(actual) == 2
    assert actual[0].journal.user.username == 'bob'
    assert actual[0].year == 1974
    assert actual[1].journal.user.username == 'bob'
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


def test_necessary_related():
    NecessaryPlanFactory()
    NecessaryPlanFactory(journal=JournalFactory(user=UserFactory(username='X')))

    actual = NecessaryPlan.objects.related()

    assert len(actual) == 1
    assert actual[0].journal.user.username == 'bob'


def test_necessary_year():
    j = JournalFactory(user=UserFactory(username='X'))
    NecessaryPlanFactory()
    NecessaryPlanFactory(year=1974, journal=j)

    actual = list(NecessaryPlan.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].journal.user.username == 'bob'


def test_necessary_items():
    j = JournalFactory(user=UserFactory(username='X'))
    NecessaryPlanFactory()
    NecessaryPlanFactory(year=1974)
    NecessaryPlanFactory(year=1974, journal=j)

    actual = NecessaryPlan.objects.items()

    assert len(actual) == 2
    assert actual[0].journal.user.username == 'bob'
    assert actual[0].year == 1974
    assert actual[0].title == 'other'
    assert actual[1].journal.user.username == 'bob'
    assert actual[1].year == 1999
    assert actual[1].title == 'other'


@pytest.mark.xfail(raises=Exception)
def test_necessary_no_dublicates():
    NecessaryPlanFactory(year=2000, title='N')
    NecessaryPlanFactory(year=2000, title='N')
