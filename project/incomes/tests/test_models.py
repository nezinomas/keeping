from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ...users.factories import UserFactory
from ..factories import IncomeFactory, IncomeTypeFactory
from ..models import Income, IncomeType
from ...journals.factories import JournalFactory
pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Income Type
# ----------------------------------------------------------------------------
def test_income_type_str():
    i = IncomeTypeFactory.build()

    assert str(i) == 'Income Type'


def test_income_type_items_journal():
    IncomeTypeFactory(title='T1', journal=JournalFactory())
    IncomeTypeFactory(title='T2', journal=JournalFactory(user=UserFactory(username='XX')))

    actual = IncomeType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


def test_income_type_items_journal_queries(django_assert_max_num_queries):
    IncomeTypeFactory()
    with django_assert_max_num_queries(1):
        qs = IncomeType.objects.items().values()



@pytest.mark.xfail
def test_income_type_unique_for_journal():
    IncomeType.objects.create(title='T', journal=JournalFactory())
    IncomeType.objects.create(title='T', journal=JournalFactory())


def test_income_type_unique_for_journals():
    u1 = UserFactory(username='X')
    u2 = UserFactory(username='Y')
    IncomeType.objects.create(title='T', journal=JournalFactory(user=u1))
    IncomeType.objects.create(title='T', journal=JournalFactory(user=u2))


# ----------------------------------------------------------------------------
#                                                                       Income
# ----------------------------------------------------------------------------
def test_income_str():
    i = IncomeFactory.build()

    assert str(i) == '1999-01-01: Income Type'


def test_income_related():
    u1 = UserFactory()
    u2 = UserFactory(username='X')
    t1 = IncomeTypeFactory(title='T1', journal=JournalFactory(user=u1))
    t2 = IncomeTypeFactory(title='T2', journal=JournalFactory(user=u2))

    IncomeFactory(income_type=t1)
    IncomeFactory(income_type=t2)

    actual = Income.objects.related()

    assert len(actual) == 1
    assert str(actual[0].income_type) == 'T1'


def test_sum_all_months(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]

    actual = list(Income.objects.sum_by_month(1999))

    assert expect == actual


def test_sum_all_months_ordering(incomes):
    actual = list(Income.objects.sum_by_month(1999))

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[1]['date'] == date(1999, 2, 1)


def test_sum_one_month(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)}
    ]

    actual = list(Income.objects.sum_by_month(1999, 1))

    assert len(expect) == 1
    assert expect == actual


def test_incomes_items():
    IncomeFactory()

    assert len(Income.objects.items()) == 1


def test_incomes_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = Income.objects.items()
        list([x['date'] for x in qs])


def test_incomes_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = Income.objects.year(1999)
        list([x['date'] for x in qs])


def test_incomes_income_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        qs = Income.objects.sum_by_month(1999)
        list([x['date'] for x in qs])

def test_summary(incomes):
    expect = [{
        'id': 1,
        'title': 'Account1',
        'i_past': Decimal(5.25),
        'i_now': Decimal(3.25),

    }, {
        'id': 2,
        'title': 'Account2',
        'i_past': Decimal(4.5),
        'i_now': Decimal(3.5),
    }]

    actual = list(Income.objects.summary(1999).order_by('account__title'))

    assert expect == actual


def test_income_month_type_sum():
    IncomeFactory(
        price=4,
        date=date(1999, 1, 2),
        income_type=IncomeTypeFactory(title='I-2')
    )
    IncomeFactory(
        price=3,
        date=date(1999, 1, 1),
        income_type=IncomeTypeFactory(title='I-2')
    )
    IncomeFactory(
        price=1,
        date=date(1974, 1, 1),
        income_type=IncomeTypeFactory(title='I-1')
    )
    IncomeFactory(
        price=2,
        date=date(1999, 1, 2),
        income_type=IncomeTypeFactory(title='I-1')
    )
    IncomeFactory(
        price=1,
        date=date(1999, 1, 1),
        income_type=IncomeTypeFactory(title='I-1')
    )

    expect = [
        {'date': date(1999, 1, 1), 'title': 'I-1', 'sum': Decimal(3)},
        {'date': date(1999, 1, 1), 'title': 'I-2', 'sum': Decimal(7)},
    ]
    actual = Income.objects.sum_by_month_and_type(1999)

    assert expect == [*actual]


def test_income_new_post_save():
    IncomeFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1000.62
    assert actual['balance'] == 1000.62


def test_income_update_post_save():
    obj = IncomeFactory()

    # update price
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['balance'] == 1.0


def test_income_post_delete():
    obj = IncomeFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    assert actual[0]['title'] == 'Account1'
    assert actual[0]['incomes'] == 0
    assert actual[0]['balance'] == 0

    assert Income.objects.all().count() == 0


def test_income_post_delete_with_update():
    IncomeFactory(price=1)

    obj = IncomeFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    assert actual[0]['title'] == 'Account1'
    assert actual[0]['incomes'] == 1.0
    assert actual[0]['balance'] == 1.0

    assert Income.objects.all().count() == 1


def test_income_new_post_save_count_qs(django_assert_max_num_queries):
    AccountFactory()
    IncomeTypeFactory()

    assert AccountBalance.objects.all().count() == 0

    with django_assert_max_num_queries(27):
        IncomeFactory()


def test_income_update_post_save_count_qs(django_assert_max_num_queries):
    IncomeTypeFactory()
    AccountBalanceFactory()

    assert AccountBalance.objects.all().count() == 1

    with django_assert_max_num_queries(25):
        IncomeFactory()


def test_income_years_sum():
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)

    actual = Income.objects.sum_by_year()

    assert actual[0]['year'] == 1998
    assert actual[0]['sum'] == 8.0

    assert actual[1]['year'] == 1999
    assert actual[1]['sum'] == 10.0


def test_income_year_sum_count_qs(django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        list([x['year'] for x in Income.objects.sum_by_year()])


def test_income_year_sum_filter():
    IncomeFactory(date=date(1999, 1, 1), price=5.0, income_type=IncomeTypeFactory(title='x'))
    IncomeFactory(date=date(1999, 1, 1), price=5.0, income_type=IncomeTypeFactory(title='x'))
    IncomeFactory(date=date(1999, 1, 1), price=15.0, income_type=IncomeTypeFactory(title='y'))

    actual = Income.objects.sum_by_year(['x'])

    assert actual[0]['year'] == 1999
    assert actual[0]['sum'] == 10.0


def test_income_year_sum_filter_two_types():
    IncomeFactory(date=date(1999, 1, 1), price=5.0, income_type=IncomeTypeFactory(title='x'))
    IncomeFactory(date=date(1999, 1, 1), price=5.0, income_type=IncomeTypeFactory(title='x'))
    IncomeFactory(date=date(1999, 1, 1), price=15.0, income_type=IncomeTypeFactory(title='y'))
    IncomeFactory(date=date(1999, 1, 1), price=20.0, income_type=IncomeTypeFactory(title='z'))

    actual = Income.objects.sum_by_year(['x', 'y'])

    assert actual[0]['year'] == 1999
    assert actual[0]['sum'] == 25.0


def test_income_year_sum_filter_count_qs(django_assert_max_num_queries):
    IncomeFactory()

    with django_assert_max_num_queries(1):
        list([x['year'] for x in Income.objects.sum_by_year(['x'])])
