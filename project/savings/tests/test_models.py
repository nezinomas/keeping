from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...incomes.factories import IncomeFactory
from ...savings.factories import (SavingBalanceFactory, SavingFactory,
                                  SavingTypeFactory)
from ...savings.models import SavingBalance
from ..models import Saving, SavingBalance, SavingType

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _savings_extra():
    SavingFactory(
        date=date(1999, 1, 1),
        price=1.0,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=1.0,
        fee=0.25,
        account=AccountFactory(title='Account2'),
        saving_type=SavingTypeFactory(title='Saving1')
    )


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
def test_saving_type_str():
    i = SavingFactory.build()

    assert str(i) == '1999-01-01: Savings'


def test_saving_type_items_user(main_user, second_user):
    SavingTypeFactory(title='T1', journal=main_user.journal)
    SavingTypeFactory(title='T2', journal=second_user.journal)

    actual = SavingType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


def test_saving_type_items_filter_closed_in_future():
    SavingTypeFactory(title='T1', closed=1998)
    SavingTypeFactory(title='T2', closed=2000)

    actual = SavingType.objects.items(year=1999)

    assert actual.count() == 1
    assert actual[0].title == 'T2'


def test_saving_type_items_filter_closed_in_future_year_from_get_user():
    SavingTypeFactory(title='T1', closed=1998)
    SavingTypeFactory(title='T2', closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T2'


def test_saving_type_day_sum_empty_month(savings):
    expect = []

    actual = list(Saving.objects.sum_by_day_and_type(1999, 2))

    assert expect == actual


def test_saving_type_items_closed_in_past(get_user):
    get_user.year = 3000
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 1


def test_saving_type_items_closed_in_future(get_user):
    get_user.year = 1000
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 2


def test_saving_type_items_closed_in_current_year(get_user):
    get_user.year = 2000
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 2


@pytest.mark.xfail
def test_saving_type_unique_for_journal(main_user):
    SavingType.objects.create(title='T1', journal=main_user.journal)
    SavingType.objects.create(title='T1', journal=main_user.journal)


def test_saving_type_unique_for_journals(main_user, second_user):
    SavingType.objects.create(title='T1', journal=main_user.journal)
    SavingType.objects.create(title='T1', journal=second_user.journal)


# ----------------------------------------------------------------------------
#                                                                       Saving
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingTypeFactory.build()

    assert str(actual) == 'Savings'


def test_saving_related(main_user, second_user):
    t1 = SavingTypeFactory(title='T1', journal=main_user.journal)
    t2 = SavingTypeFactory(title='T2', journal=second_user.journal)

    SavingFactory(saving_type=t1)
    SavingFactory(saving_type=t2)

    actual = Saving.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == 'T1'


def test_saving_items():
    SavingFactory()

    assert len(Saving.objects.items()) == 1


def test_saving_month_sum(savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.sum_by_month_and_type(1999))

    assert expect == actual


def test_saving_type_day_sum(savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.sum_by_day_and_type(1999, 1))

    assert expect == actual


def test_saving_day_sum(_savings_extra):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(2.0)},
    ]

    actual = list(Saving.objects.sum_by_day(1999, 1))

    assert expect == actual


def test_saving_months_sum(savings):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(5.75)}]

    actual = list(Saving.objects.sum_by_month(1999))

    assert expect == actual


def test_saving_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.items().values()


def test_saving_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.year(1999).values()


def test_saving_month_saving_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.sum_by_month(1999).values()


def test_saving_month_type_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.sum_by_month_and_type(1999).values()


def test_saving_day_saving_type_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.sum_by_day_and_type(1999, 1).values()


def test_saving_day_saving_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.sum_by_day(1999, 1).values()


@freeze_time('1999-06-01')
def test_saving_last_months():
    SavingFactory(date=date(1998, 11, 30), price=3)
    SavingFactory(date=date(1998, 12, 31), price=4)
    SavingFactory(date=date(1999, 1, 1), price=7)

    actual = Saving.objects.last_months(6)

    assert actual['sum'] == 11.0


@freeze_time('1999-06-01')
def test_saving_last_months_qs_count(django_assert_max_num_queries):
    SavingFactory(date=date(1999, 1, 1), price=2)

    with django_assert_max_num_queries(1):
        print(Saving.objects.last_months())


def test_saving_post_save():
    SavingFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account1'
    assert actual[0]['expenses'] == 150.0
    assert actual[0]['balance'] == -150.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 144.45
    assert actual[0]['fees'] == 5.55
    assert actual[0]['incomes'] == 150.0


def test_saving_post_save_update():
    obj = SavingFactory()

    # update price
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.price = 10
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=obj.account.pk)
    assert actual.expenses == 10.0
    assert actual.balance == -10.0

    actual = SavingBalance.objects.get(saving_type_id=obj.saving_type.pk)
    assert actual.invested == 4.45
    assert actual.fees == 5.55
    assert actual.incomes == 10.0


def test_saving_post_save_first_record():
    _a = AccountFactory(title='A')
    _s = SavingTypeFactory(title='S')

    SavingFactory(saving_type=_s, account=_a, price=4, date=date(1998, 1, 1), fee=0.25)
    IncomeFactory(account=_a, price=3, date=date(1998, 1, 1))

    # truncate table
    SavingBalance.objects.all().delete()
    AccountBalance.objects.all().delete()

    SavingFactory(saving_type=_s, account=_a, price=1, fee=0.25)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == 'A'
    assert actual.past == -1.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -2.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 4.0
    assert actual.past_fee == 0.25
    assert actual.fees == 0.5
    assert actual.invested == 4.5
    assert actual.incomes == 5.0


def test_saving_post_save_new():
    _a = AccountFactory(title='A')
    _s = SavingTypeFactory(title='S')

    SavingFactory(saving_type=_s, account=_a, price=1, fee=0.25)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == 'A'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_saving_post_save_different_types():
    s1 = SavingTypeFactory(title='1')
    s2 = SavingTypeFactory(title='2')

    SavingFactory(saving_type=s1, price=150)
    SavingFactory(saving_type=s2, price=250)

    actual = Saving.objects.all()
    assert actual.count() == 2
    print('------------------------------------------------------------------------', Saving.objects.values())
    actual = AccountBalance.objects.all()
    assert actual.count() == 1

    actual = AccountBalance.objects.last()
    assert actual.incomes == 0.0
    assert actual.expenses == -400.0

    actual = SavingBalance.objects.all()
    assert actual.count() == 2

    actual = SavingBalance.objects.get(year=1999, saving_type_id=s1.pl)
    assert actual.incomes == 150.0
    assert actual.fees == 5.55
    assert actual.invested == 144.45

    actual = SavingBalance.objects.get(year=1999, saving_type_id=s2.pl)
    assert actual.incomes == 250.0
    assert actual.fees == 5.55
    assert actual.invested == 244.45


def test_saving_post_save_update_nothing_changed():
    _a = AccountFactory(title='A')
    _s = SavingTypeFactory(title='S')

    obj = SavingFactory(saving_type=_s, account=_a, price=1, fee=0.25)

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == 'A'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_saving_post_save_update_changed_saving_type():
    _a = AccountFactory(title='A')
    _s = SavingTypeFactory(title='S')
    _s_new = SavingTypeFactory(title='S-New')

    obj = SavingFactory(saving_type=_s, account=_a, price=1, fee=0.25)

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.saving_type = _s_new
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == 'A'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_s_new.pk, year=1999)
    assert actual.saving_type.title == 'S-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_saving_post_save_update_changed_account():
    _a = AccountFactory(title='A')
    _a_new = AccountFactory(title='A-New')
    _s = SavingTypeFactory(title='S')

    obj = SavingFactory(saving_type=_s, account=_a, price=1, fee=0.25)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == 'A'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.account = _a_new
    obj_update.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=_a_new.pk, year=1999)
    assert actual.account.title == 'A-New'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_saving_post_save_update_changed_account_and_saving_type():
    _a = AccountFactory(title='A')
    _a_new = AccountFactory(title='A-New')
    _s = SavingTypeFactory(title='S')
    _s_new = SavingTypeFactory(title='S-New')

    obj = SavingFactory(saving_type=_s, account=_a, price=1, fee=0.25)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == 'A'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.account = _a_new
    obj_update.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=_a_new.pk, year=1999)
    assert actual.account.title == 'A-New'
    assert actual.past == 0.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.0
    assert actual.invested == 0.0
    assert actual.incomes == 0.0

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == 'S-New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fees == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_saving_post_delete():
    obj = SavingFactory()

    Saving.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account1'
    assert actual[0]['expenses'] == 0
    assert actual[0]['balance'] == 0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 0
    assert actual[0]['fees'] == 0
    assert actual[0]['incomes'] == 0

    assert Saving.objects.all().count() == 0


def test_saving_post_delete_with_update():
    SavingFactory(price=10)

    obj = SavingFactory()
    Saving.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'Account1'
    assert actual[0]['expenses'] == 10.0
    assert actual[0]['balance'] == -10.0

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['invested'] == 4.45
    assert actual[0]['fees'] == 5.55
    assert actual[0]['incomes'] == 10.0

    assert Saving.objects.all().count() == 1


def test_savings_incomes(savings):
    actual = Saving.objects.incomes()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['incomes'] == 1.25
    assert actual[0]['fees'] == 0.25

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['incomes'] == 0.25
    assert actual[1]['fees'] == 0.0

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['incomes'] == 3.5
    assert actual[2]['fees'] == 0.5

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['incomes'] == 2.25
    assert actual[3]['fees'] == 0.25


def test_savings_expenses(savings):
    actual = Saving.objects.expenses()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['expenses'] == 1.25

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['expenses'] == 0.25

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['expenses'] == 3.5

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['expenses'] == 2.25


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
def test_saving_balance_init():
    actual = SavingBalanceFactory.build()

    assert str(actual.saving_type) == 'Savings'

    assert actual.past_amount == 2.0
    assert actual.past_fee == 2.1
    assert actual.fees == 2.2
    assert actual.invested == 2.3
    assert actual.incomes == 2.4
    assert actual.market_value == 2.5
    assert actual.profit_incomes_proc == 2.6
    assert actual.profit_incomes_sum == 2.7
    assert actual.profit_invested_proc == 2.8
    assert actual.profit_invested_sum == 2.9


def test_saving_balance_str():
    actual = SavingBalanceFactory.build()

    assert str(actual) == 'Savings'


@pytest.mark.django_db
def test_saving_balance_related_for_user(main_user, second_user):
    s1 = SavingTypeFactory(title='S1', journal=main_user.journal)
    s2 = SavingTypeFactory(title='S2', journal=second_user.journal)

    SavingFactory(saving_type=s1)
    SavingFactory(saving_type=s2)

    actual = SavingBalance.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == 'S1'
    assert actual[0].saving_type.journal.title == 'bob Journal'
    assert actual[0].saving_type.journal.users.first().username == 'bob'


@pytest.mark.django_db
def test_saving_balance_year():
    SavingBalanceFactory(year=1998)
    SavingBalanceFactory(year=1999)
    SavingBalanceFactory(year=2000)

    actual = SavingBalance.objects.year(1999)

    assert len(actual) == 1


def test_saving_balance_items_queries(django_assert_num_queries):
    s1 = SavingTypeFactory(title='s1')
    s2 = SavingTypeFactory(title='s2')

    SavingBalanceFactory(saving_type=s1)
    SavingBalanceFactory(saving_type=s2)

    with django_assert_num_queries(1):
        list(SavingBalance.objects.items().values())


def test_saving_balance_new_post_save_account_balace():
    SavingFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 0.0
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 150.0
    assert actual['balance'] == -150.0


def test_saving_balance_new_post_save_saving_balance():
    SavingFactory()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Savings'

    assert round(actual['incomes'], 2) == 150
    assert round(actual['fees'], 2) == 5.55
    assert round(actual['invested'], 2) == 144.45


def test_saving_balance_filter_by_one_type():
    SavingFactory(saving_type=SavingTypeFactory(title='1', type='x'))
    SavingFactory(saving_type=SavingTypeFactory(title='2', type='z'))

    actual = SavingBalance.objects.year(1999, ['x'])

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == '1'

    assert round(actual['incomes'], 2) == 150
    assert round(actual['fees'], 2) == 5.55
    assert round(actual['invested'], 2) == 144.45


def test_saving_balance_filter_by_few_types():
    SavingFactory(saving_type=SavingTypeFactory(title='1', type='x'))
    SavingFactory(saving_type=SavingTypeFactory(title='2', type='y'))
    SavingFactory(saving_type=SavingTypeFactory(title='3', type='z'))

    actual = SavingBalance.objects.year(1999, ['x', 'y'])

    assert actual.count() == 2

    assert actual[0]['title'] == '1'
    assert actual[1]['title'] == '2'


@freeze_time('1999-1-1')
def test_sum_by_type_funds():
    f = SavingTypeFactory(title='F', type='funds')

    SavingFactory(saving_type=f, price=1)
    SavingFactory(saving_type=f, price=10)

    actual = list(SavingBalance.objects.sum_by_type())

    assert actual == [{'year': 1999, 'invested': 11.0, 'profit': -11.0, 'type': 'funds'}]


@freeze_time('1999-1-1')
def test_sum_by_type_shares():
    f = SavingTypeFactory(title='F', type='shares')

    SavingFactory(saving_type=f, price=1)
    SavingFactory(saving_type=f, price=10)

    actual = list(SavingBalance.objects.sum_by_type())

    assert actual == [{'year': 1999, 'invested': 11.0, 'profit': -11.0, 'type': 'shares'}]


@freeze_time('1999-1-1')
def test_sum_by_type_pensions():
    f = SavingTypeFactory(title='F', type='pensions')

    SavingFactory(saving_type=f, price=1)
    SavingFactory(saving_type=f, price=10)

    actual = list(SavingBalance.objects.sum_by_type())

    assert actual == [{'year': 1999, 'invested': 11.0, 'profit': -11.0, 'type': 'pensions'}]


@freeze_time('1999-1-1')
def test_sum_by_year():
    f = SavingTypeFactory(title='F', type='funds')
    p = SavingTypeFactory(title='P', type='pensions')
    s = SavingTypeFactory(title='S', type='shares')

    SavingFactory(saving_type=f, price=1)
    SavingFactory(saving_type=p, price=2)
    SavingFactory(saving_type=s, price=4)

    actual = list(SavingBalance.objects.sum_by_year())

    assert actual == [{'year': 1999, 'invested': 7.0, 'profit': -7.0}]
