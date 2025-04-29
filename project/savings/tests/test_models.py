from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingBalanceFactory, SavingFactory, SavingTypeFactory
from ...savings.models import SavingBalance
from ..models import Saving, SavingBalance, SavingType

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _savings_extra():
    SavingFactory(
        date=date(1999, 1, 1),
        price=1,
        fee=0.25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=1,
        fee=0.25,
        account=AccountFactory(title="Account2"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
def test_saving_type_str():
    i = SavingFactory.build()

    assert str(i) == "1999-01-01: Savings"


def test_saving_type_get_absolute_url():
    obj = SavingTypeFactory()

    assert obj.get_absolute_url() == reverse(
        "savings:type_update", kwargs={"pk": obj.pk}
    )


def test_saving_type_items_user(second_user):
    SavingTypeFactory(title="T1")
    SavingTypeFactory(title="T2", journal=second_user.journal)

    actual = SavingType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == "T1"


def test_saving_type_items_filter_closed_in_future():
    SavingTypeFactory(title="T1", closed=1998)
    SavingTypeFactory(title="T2", closed=2000)

    actual = SavingType.objects.items(year=1999)

    assert actual.count() == 1
    assert actual[0].title == "T2"


def test_saving_type_items_filter_closed_in_future_year_from_get_user():
    SavingTypeFactory(title="T1", closed=1998)
    SavingTypeFactory(title="T2", closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == "T2"


def test_saving_type_day_sum_empty_month(savings):
    expect = []

    actual = list(Saving.objects.sum_by_day_and_type(1999, 2))

    assert expect == actual


def test_saving_type_items_closed_in_past(main_user):
    main_user.year = 3000
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 1


def test_saving_type_items_closed_in_future(main_user):
    main_user.year = 1000
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 2


def test_saving_type_items_closed_in_current_year(main_user):
    main_user.year = 2000
    SavingTypeFactory(title="S1")
    SavingTypeFactory(title="S2", closed=2000)

    actual = SavingType.objects.items()

    assert actual.count() == 2


@pytest.mark.xfail
def test_saving_type_unique_for_journal(main_user):
    SavingType.objects.create(title="T1", journal=main_user.journal)
    SavingType.objects.create(title="T1", journal=main_user.journal)


def test_saving_type_unique_for_journals(main_user, second_user):
    SavingType.objects.create(title="T1", journal=main_user.journal)
    SavingType.objects.create(title="T1", journal=second_user.journal)


# ----------------------------------------------------------------------------
#                                                                       Saving
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingTypeFactory.build()

    assert str(actual) == "Savings"


def test_saving_get_absolute_url():
    obj = SavingFactory()

    assert obj.get_absolute_url() == reverse("savings:update", kwargs={"pk": obj.pk})


def test_saving_related(second_user):
    t1 = SavingTypeFactory(title="T1")
    t2 = SavingTypeFactory(title="T2", journal=second_user.journal)

    SavingFactory(saving_type=t1)
    SavingFactory(saving_type=t2)

    actual = Saving.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == "T1"


def test_saving_items():
    SavingFactory()

    assert len(Saving.objects.items()) == 1


def test_saving_years_sum():
    SavingFactory(date=date(1998, 1, 1), price=4.0)
    SavingFactory(date=date(1998, 1, 1), price=4.0)
    SavingFactory(date=date(1999, 1, 1), price=5.0)
    SavingFactory(date=date(1999, 1, 1), price=5.0)

    actual = Saving.objects.sum_by_year()

    assert actual[0]["year"] == 1998
    assert actual[0]["sum"] == 8.0

    assert actual[1]["year"] == 1999
    assert actual[1]["sum"] == 10.0


def test_saving_year_sum_count_qs(django_assert_max_num_queries):
    SavingFactory()

    with django_assert_max_num_queries(1):
        actual = [x["year"] for x in Saving.objects.sum_by_year()]
        assert len(list(actual)) == 1


def test_saving_month_sum(savings):
    expect = [
        {"date": date(1999, 1, 1), "sum": 350, "title": "Saving1"},
        {"date": date(1999, 1, 1), "sum": 225, "title": "Saving2"},
    ]

    actual = list(Saving.objects.sum_by_month_and_type(1999))

    assert expect == actual


def test_saving_type_day_sum(savings):
    expect = [
        {"date": date(1999, 1, 1), "sum": 350, "title": "Saving1"},
        {"date": date(1999, 1, 1), "sum": 225, "title": "Saving2"},
    ]

    actual = list(Saving.objects.sum_by_day_and_type(1999, 1))

    assert expect == actual


def test_saving_day_sum(_savings_extra):
    expect = [
        {"date": date(1999, 1, 1), "sum": 2, "title": "Taupymas"},
    ]

    actual = list(Saving.objects.sum_by_day(1999, 1))

    assert expect == actual


def test_saving_months_sum(savings):
    expect = [{"date": date(1999, 1, 1), "sum": 575, "title": "savings"}]

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


@time_machine.travel("1999-06-01")
def test_saving_last_months():
    SavingFactory(date=date(1998, 11, 30), price=3)
    SavingFactory(date=date(1998, 12, 31), price=4)
    SavingFactory(date=date(1999, 1, 1), price=7)

    actual = Saving.objects.last_months(6)

    assert actual["sum"] == 11


@time_machine.travel("1999-06-01")
def test_saving_last_months_qs_count(django_assert_max_num_queries):
    SavingFactory(date=date(1999, 1, 1), price=2)

    with django_assert_max_num_queries(1):
        print(Saving.objects.last_months())


def test_saving_post_save():
    SavingFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0].account.title == "Account1"
    assert actual[0].expenses == 150
    assert actual[0].balance == -150

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0].fee == 5
    assert actual[0].incomes == 150


def test_saving_post_save_update():
    obj = SavingFactory()

    # update price
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.price = 10
    obj_update.fee = 1
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.get(saving_type_id=obj.saving_type.pk, year=1999)
    assert actual.fee == 1
    assert actual.incomes == 10


def test_saving_post_save_first_record():
    _a = AccountFactory(title="A")
    _s = SavingTypeFactory(title="S")

    SavingFactory(saving_type=_s, account=_a, price=4, date=date(1998, 1, 1), fee=2)
    IncomeFactory(account=_a, price=3, date=date(1998, 1, 1))

    # truncate table
    SavingBalance.objects.all().delete()
    AccountBalance.objects.all().delete()

    SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == -1
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -11

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 4
    assert actual.past_fee == 2
    assert actual.fee == 4
    assert actual.incomes == 14


def test_saving_post_save_new():
    _a = AccountFactory(title="A")
    _s = SavingTypeFactory(title="S")

    SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10


def test_saving_post_save_different_types():
    s1 = SavingTypeFactory(title="1")
    s2 = SavingTypeFactory(title="2")

    SavingFactory(saving_type=s1, price=150)
    SavingFactory(saving_type=s2, price=250)

    actual = Saving.objects.all()
    assert actual.count() == 2

    actual = AccountBalance.objects.all()
    assert actual.count() == 2

    actual = AccountBalance.objects.first()
    assert actual.incomes == 0
    assert actual.expenses == 400

    actual = SavingBalance.objects.all()
    assert actual.count() == 4

    actual = SavingBalance.objects.get(year=1999, saving_type_id=s1.pk)
    assert actual.incomes == 150
    assert actual.fee == 5

    actual = SavingBalance.objects.get(year=1999, saving_type_id=s2.pk)
    assert actual.incomes == 250
    assert actual.fee == 5


def test_saving_post_save_update_nothing_changed():
    _a = AccountFactory(title="A")
    _s = SavingTypeFactory(title="S")

    obj = SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10


def test_saving_post_save_update_changed_saving_type():
    _a = AccountFactory(title="A")
    _s = SavingTypeFactory(title="S")
    _s_new = SavingTypeFactory(title="S-New")

    obj = SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.saving_type = _s_new
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.filter(saving_type_id=_s.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_s_new.pk, year=1999)
    assert actual.saving_type.title == "S-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10


def test_saving_post_save_update_changed_account():
    _a = AccountFactory(title="A")
    _a_new = AccountFactory(title="A-New")
    _s = SavingTypeFactory(title="S")

    obj = SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.account = _a_new
    obj_update.save()

    actual = AccountBalance.objects.filter(account_id=_a.pk, year=1999)
    assert actual.count() == 0

    actual = AccountBalance.objects.get(account_id=_a_new.pk, year=1999)
    assert actual.account.title == "A-New"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10


def test_saving_post_save_update_changed_account_and_saving_type():
    _a = AccountFactory(title="A")
    _a_new = AccountFactory(title="A-New")
    _s = SavingTypeFactory(title="S")
    _s_new = SavingTypeFactory(title="S-New")

    obj = SavingFactory(saving_type=_s, account=_a, price=10, fee=2)

    actual = AccountBalance.objects.get(account_id=_a.pk, year=1999)
    assert actual.account.title == "A"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.get(saving_type_id=_s.pk, year=1999)
    assert actual.saving_type.title == "S"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10

    # update saving change
    obj_update = Saving.objects.get(pk=obj.pk)
    obj_update.account = _a_new
    obj_update.saving_type = _s_new
    obj_update.save()

    actual = AccountBalance.objects.filter(account_id=_a.pk, year=1999)
    assert actual.count() == 0

    actual = AccountBalance.objects.get(account_id=_a_new.pk, year=1999)
    assert actual.account.title == "A-New"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10

    actual = SavingBalance.objects.filter(saving_type_id=_s.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_s_new.pk, year=1999)
    assert actual.saving_type.title == "S-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.incomes == 10


def test_saving_post_delete():
    obj = SavingFactory()

    Saving.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.year(1999)
    assert actual.count() == 0

    assert Saving.objects.all().count() == 0


def test_saving_post_delete_with_update():
    SavingFactory(price=10)

    obj = SavingFactory()
    Saving.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0].account.title == "Account1"
    assert actual[0].expenses == 10
    assert actual[0].balance == -10

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0].fee == 5
    assert actual[0].incomes == 10

    assert Saving.objects.all().count() == 1


def test_savings_incomes(savings):
    SavingFactory(
        date=date(1999, 1, 1),
        price=225,
        fee=25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving2"),
    )

    actual = Saving.objects.incomes()

    assert actual[0]["year"] == 1970
    assert actual[0]["category_id"] == 1
    assert actual[0]["incomes"] == 125
    assert actual[0]["fee"] == 25

    assert actual[1]["year"] == 1970
    assert actual[1]["category_id"] == 2
    assert actual[1]["incomes"] == 25
    assert actual[1]["fee"] == 0

    assert actual[2]["year"] == 1999
    assert actual[2]["category_id"] == 1
    assert actual[2]["incomes"] == 350
    assert actual[2]["fee"] == 50

    assert actual[3]["year"] == 1999
    assert actual[3]["category_id"] == 2
    assert actual[3]["incomes"] == 450
    assert actual[3]["fee"] == 50


def test_savings_expenses(savings):
    actual = Saving.objects.expenses()

    assert actual[0]["year"] == 1970
    assert actual[0]["category_id"] == 1
    assert actual[0]["expenses"] == 125

    assert actual[1]["year"] == 1970
    assert actual[1]["category_id"] == 2
    assert actual[1]["expenses"] == 25

    assert actual[2]["year"] == 1999
    assert actual[2]["category_id"] == 1
    assert actual[2]["expenses"] == 350

    assert actual[3]["year"] == 1999
    assert actual[3]["category_id"] == 2
    assert actual[3]["expenses"] == 225


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
def test_saving_balance_init():
    actual = SavingBalanceFactory.build()

    assert str(actual.saving_type) == "Savings"

    assert actual.past_amount == 20
    assert actual.past_fee == 21
    assert actual.fee == 22
    assert actual.incomes == 24
    assert actual.market_value == 25
    assert actual.profit_sum == 29


def test_saving_balance_str():
    actual = SavingBalanceFactory.build()

    assert str(actual) == "Savings"


@pytest.mark.django_db
def test_saving_balance_related_for_user(second_user):
    s1 = SavingTypeFactory(title="S1")
    s2 = SavingTypeFactory(title="S2", journal=second_user.journal)

    SavingFactory(saving_type=s1)
    SavingFactory(saving_type=s2)

    actual = SavingBalance.objects.related()

    assert len(actual) == 2
    assert str(actual[0].saving_type) == "S1"
    assert actual[0].saving_type.journal.title == "bob Journal"
    assert actual[0].saving_type.journal.users.first().username == "bob"


@pytest.mark.django_db
def test_saving_balance_year():
    SavingBalanceFactory(year=1998)
    SavingBalanceFactory(year=1999)
    SavingBalanceFactory(year=2000)

    actual = SavingBalance.objects.year(1999)

    assert len(actual) == 1


def test_saving_balance_items_queries(django_assert_num_queries):
    s1 = SavingTypeFactory(title="s1")
    s2 = SavingTypeFactory(title="s2")

    SavingBalanceFactory(saving_type=s1)
    SavingBalanceFactory(saving_type=s2)

    with django_assert_num_queries(1):
        list(SavingBalance.objects.items().values())


def test_saving_balance_new_post_save_account_balace():
    SavingFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.past == 0
    assert actual.incomes == 0
    assert actual.expenses == 150
    assert actual.balance == -150


def test_saving_balance_new_post_save_saving_balance():
    SavingFactory()

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.saving_type.title == "Savings"

    assert actual.incomes == 150
    assert actual.fee == 5


def test_saving_balance_filter_by_one_type():
    SavingFactory(saving_type=SavingTypeFactory(title="1", type="x"))
    SavingFactory(saving_type=SavingTypeFactory(title="2", type="z"))

    actual = SavingBalance.objects.year(1999, ["x"])

    assert actual.count() == 1

    actual = actual[0]

    assert actual.saving_type.title == "1"

    assert actual.incomes == 150
    assert actual.fee == 5


def test_saving_balance_filter_by_few_types():
    SavingFactory(saving_type=SavingTypeFactory(title="1", type="x"))
    SavingFactory(saving_type=SavingTypeFactory(title="2", type="y"))
    SavingFactory(saving_type=SavingTypeFactory(title="3", type="z"))

    actual = SavingBalance.objects.year(1999, ["x", "y"])

    assert actual.count() == 2

    assert actual[0].saving_type.title == "1"
    assert actual[1].saving_type.title == "2"


@time_machine.travel("1999-1-1")
def test_sum_by_type_funds():
    f = SavingTypeFactory(title="F", type="funds")

    SavingFactory(saving_type=f, price=1, fee=1)
    SavingFactory(saving_type=f, price=10, fee=1)

    actual = list(SavingBalance.objects.sum_by_type())

    assert actual == [
        {"year": 1999, "incomes": 11, "profit": -13, "fee": 2, "type": "funds"},
        {"year": 2000, "incomes": 11, "profit": -13, "fee": 2, "type": "funds"},
    ]


@time_machine.travel("1999-1-1")
def test_sum_by_type_shares():
    f = SavingTypeFactory(title="F", type="shares")

    SavingFactory(saving_type=f, price=1, fee=1)
    SavingFactory(saving_type=f, price=10, fee=1)

    actual = list(SavingBalance.objects.sum_by_type())

    assert actual == [
        {"year": 1999, "incomes": 11, "profit": -13, "fee": 2, "type": "shares"},
        {"year": 2000, "incomes": 11, "profit": -13, "fee": 2, "type": "shares"},
    ]


@time_machine.travel("1999-1-1")
def test_sum_by_type_pensions():
    f = SavingTypeFactory(title="F", type="pensions")

    SavingFactory(saving_type=f, price=1, fee=1)
    SavingFactory(saving_type=f, price=10, fee=1)

    actual = list(SavingBalance.objects.sum_by_type())

    assert actual == [
        {"year": 1999, "incomes": 11, "profit": -13, "fee": 2, "type": "pensions"},
        {"year": 2000, "incomes": 11, "profit": -13, "fee": 2, "type": "pensions"},
    ]


@time_machine.travel("1999-1-1")
def test_sum_by_year():
    f = SavingTypeFactory(title="F", type="funds")
    p = SavingTypeFactory(title="P", type="pensions")
    s = SavingTypeFactory(title="S", type="shares")

    SavingFactory(saving_type=f, price=1, fee=0)
    SavingFactory(saving_type=p, price=2, fee=0)
    SavingFactory(saving_type=s, price=4, fee=0)

    actual = list(SavingBalance.objects.sum_by_year())

    assert actual == [
        {"year": 1999, "incomes": 7, "profit": -7},
        {"year": 2000, "incomes": 7, "profit": -7},
    ]


def test_saving_balance_sorting():
    s1 = SavingTypeFactory(title="1")
    s2 = SavingTypeFactory(title="2")

    SavingBalanceFactory(year=2000, saving_type=s2)
    SavingBalanceFactory(year=1999, saving_type=s2)
    SavingBalanceFactory(year=2000, saving_type=s1)
    SavingBalanceFactory(year=1999, saving_type=s1)

    actual = SavingBalance.objects.related()

    assert actual[0].year == 1999
    assert actual[0].saving_type == s1
    assert actual[1].year == 1999
    assert actual[1].saving_type == s2
    assert actual[2].year == 2000
    assert actual[2].saving_type == s1
    assert actual[3].year == 2000
    assert actual[3].saving_type == s2