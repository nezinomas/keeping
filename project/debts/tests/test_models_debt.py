from datetime import date as dt

import pytest

from ...accounts.factories import AccountBalance, AccountFactory
from ...accounts.services.model_services import AccountBalanceModelService
from ...incomes.factories import IncomeFactory
from ...journals.factories import JournalFactory
from ..factories import BorrowFactory, LendFactory
from ..models import Debt
from ..services.model_services import DebtModelService

pytestmark = pytest.mark.django_db


def test_debt_str():
    v = LendFactory.build(name="X")

    assert str(v) == "X"


def test_debt_fields():
    assert Debt._meta.get_field("date")
    assert Debt._meta.get_field("debt_type")
    assert Debt._meta.get_field("name")
    assert Debt._meta.get_field("price")
    assert Debt._meta.get_field("returned")
    assert Debt._meta.get_field("closed")
    assert Debt._meta.get_field("account")
    assert Debt._meta.get_field("journal")
    assert Debt._meta.get_field("remark")


def test_lend_related(main_user, second_user):
    o = LendFactory()
    LendFactory(journal=second_user.journal)

    actual = Debt.objects.related(main_user, "lend")

    assert len(actual) == 1
    assert str(actual[0]) == str(o)


def test_borrow_related(main_user, second_user):
    o = BorrowFactory()
    BorrowFactory(journal=second_user.journal)

    actual = Debt.objects.related(main_user, "borrow")

    assert len(actual) == 1
    assert str(actual[0]) == str(o)


def test_debt_related_queries(main_user, django_assert_num_queries):
    LendFactory()
    LendFactory()

    with django_assert_num_queries(1):
        list(x.account.title for x in list(Debt.objects.related(main_user, "lend")))


def test_debt_sort(main_user):
    o1 = LendFactory(date=dt(1999, 1, 2))
    o2 = LendFactory(date=dt(1999, 12, 13))

    actual = Debt.objects.related(main_user, "lend")

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


def test_debt_items(main_user, second_user):
    o = LendFactory()
    LendFactory(name="X1", journal=second_user.journal)

    actual = DebtModelService(main_user, "lend").items()

    assert actual.count() == 1
    assert str(actual[0]) == str(o)


def test_debt_year(main_user):
    o = LendFactory(name="N1", date=dt(1999, 2, 3))
    LendFactory(name="N2", date=dt(2999, 2, 3), price=2)

    actual = DebtModelService(main_user, "lend").year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == str(o)
    assert actual[0].name == o.name
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == 100


def test_debt_year_and_not_closed(main_user):
    o1 = LendFactory(date=dt(1974, 1, 1), closed=False)
    LendFactory(date=dt(1974, 12, 1), closed=True)
    o2 = LendFactory(date=dt(1999, 1, 1), closed=False)
    o3 = LendFactory(date=dt(1999, 12, 1), closed=True)

    actual = DebtModelService(main_user, "lend").year(1999)

    assert actual.count() == 3

    assert actual[0].date == o3.date
    assert actual[1].date == o2.date
    assert actual[2].date == o1.date


def test_lend_post_save_new(main_user):
    LendFactory()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 100.0
    assert actual.balance == -100.0


def test_borrow_post_save_new(main_user):
    BorrowFactory()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 100.0
    assert actual.expenses == 0.0
    assert actual.balance == 100.0


def test_lend_post_save_update():
    obj = LendFactory(price=1)

    actual = AccountBalance.objects.first()
    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0

    # update object
    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.price = 2
    obj_update.save()

    actual = AccountBalance.objects.first()
    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 2.0
    assert actual.balance == -2.0


def test_borrow_post_save_update():
    obj = BorrowFactory(price=1)

    actual = AccountBalance.objects.first()
    assert actual.account.title == "Account1"
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0

    # update object
    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.price = 2
    obj_update.save()

    actual = AccountBalance.objects.first()
    assert actual.account.title == "Account1"
    assert actual.incomes == 2.0
    assert actual.expenses == 0.0
    assert actual.balance == 2.0


def test_lend_post_save_first_record(main_user):
    a = AccountFactory()
    j = JournalFactory()

    # past records
    IncomeFactory(date=dt(1998, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    Debt.objects.create(
        date=dt(1999, 1, 1), price=1, account=a, journal=j, debt_type="lend"
    )

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.past == 5.0
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == 4.0


def test_borrow_post_save_first_record(main_user):
    a = AccountFactory()
    j = JournalFactory()

    # past records
    IncomeFactory(date=dt(1998, 1, 1), price=5)

    AccountBalance.objects.all().delete()

    Debt.objects.create(
        date=dt(1999, 1, 1), price=1, account=a, journal=j, debt_type="borrow"
    )

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.past == 5.0
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 6.0


def test_lend_post_save_update_with_nothing_changed(main_user):
    obj = LendFactory(price=5)

    # update price
    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_borrow_post_save_update_with_nothing_changed(main_user):
    obj = BorrowFactory(price=5)

    # update price
    obj_update = Debt.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == "Account1"
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0


def test_lend_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title="XXX")

    obj = LendFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0

    # update price
    obj_new = Debt.objects.get(account_id=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=account_new.pk, year=1999)
    assert actual.account.title == "XXX"
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_borrow_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title="XXX")

    obj = BorrowFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0

    # update price
    obj_new = Debt.objects.get(account_id=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    fail = False
    try:
        actual = AccountBalance.objects.get(account_id=account_old.pk, year=1999)
    except AccountBalance.DoesNotExist:
        fail = True

    assert fail

    actual = AccountBalance.objects.get(account_id=account_new.pk, year=1999)
    assert actual.account.title == "XXX"
    assert actual.incomes == 5.0
    assert actual.expenses == 0.0
    assert actual.balance == 5.0


def test_lend_post_delete():
    obj = LendFactory(price=10)

    actual = AccountBalance.objects.first()
    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 10.0
    assert actual.balance == -10.0

    Debt.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.first()
    assert not actual


def test_borrow_post_delete():
    obj = BorrowFactory(price=10)

    actual = AccountBalance.objects.first()
    assert actual.account.title == "Account1"
    assert actual.incomes == 10.0
    assert actual.expenses == 0.0
    assert actual.balance == 10.0

    Debt.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.first()
    assert not actual


def test_lend_post_delete_with_updt():
    obj = LendFactory(price=1)
    obj_delete = LendFactory(price=10)

    assert AccountBalance.objects.count() == 2
    assert Debt.objects.count() == 2

    actual = AccountBalance.objects.get(account_id=obj.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 11.0
    assert actual.balance == -11.0

    # delete second debt
    Debt.objects.get(pk=obj_delete.pk).delete()

    actual = AccountBalance.objects.get(account_id=obj.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 0.0
    assert actual.expenses == 1.0
    assert actual.balance == -1.0


def test_borrow_post_delete_with_updt():
    obj = BorrowFactory(price=1)
    obj_del = BorrowFactory(price=10)

    assert AccountBalance.objects.count() == 2
    assert Debt.objects.count() == 2

    actual = AccountBalance.objects.get(account_id=obj.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 11.0
    assert actual.expenses == 0.0
    assert actual.balance == 11.0

    # delete second debt
    Debt.objects.get(pk=obj_del.pk).delete()

    actual = AccountBalance.objects.get(account_id=obj.pk, year=1999)
    assert actual.account.title == "Account1"
    assert actual.incomes == 1.0
    assert actual.expenses == 0.0
    assert actual.balance == 1.0


def test_debt_unique_users(second_user):
    LendFactory(name="T1")
    LendFactory(name="T1", journal=second_user.journal)


def test_debt_sum_all_months(main_user):
    LendFactory(date=dt(1999, 1, 1), price=1, returned=1)
    LendFactory(date=dt(1999, 1, 2), price=2, returned=1)
    LendFactory(date=dt(1999, 2, 1), price=4, returned=1)
    LendFactory(date=dt(1999, 2, 2), price=1, returned=1)
    LendFactory(date=dt(1999, 1, 1), closed=True)
    LendFactory(date=dt(1974, 1, 1))

    expect = [
        {"date": dt(1999, 1, 1), "sum_debt": 3, "sum_return": 2, "title": "lend"},
        {"date": dt(1999, 2, 1), "sum_debt": 5, "sum_return": 2, "title": "lend"},
    ]

    actual = list(DebtModelService(main_user, "lend").sum_by_month(1999))

    assert expect == actual


def test_debt_sum_all_months_with_closed(main_user):
    LendFactory(date=dt(1999, 1, 1), price=1, returned=1)
    LendFactory(date=dt(1999, 1, 2), price=2, returned=1)
    LendFactory(date=dt(1999, 2, 1), price=4, returned=1)
    LendFactory(date=dt(1999, 2, 2), price=1, returned=1)
    LendFactory(date=dt(1999, 1, 1), price=2, returned=2, closed=True)
    LendFactory(date=dt(1974, 1, 1))

    expect = [
        {"date": dt(1999, 1, 1), "sum_debt": 5, "sum_return": 4, "title": "lend"},
        {"date": dt(1999, 2, 1), "sum_debt": 5, "sum_return": 2, "title": "lend"},
    ]

    actual = list(DebtModelService(main_user, "lend").sum_by_month(1999, closed=True))

    assert expect == actual


def test_debt_sum_all_months_ordering(main_user, second_user):
    LendFactory(date=dt(1999, 1, 1), price=1)
    LendFactory(date=dt(1999, 1, 2), price=2)
    LendFactory(date=dt(1999, 1, 2), price=2, journal=second_user.journal)
    LendFactory(date=dt(1999, 2, 1), price=4)
    LendFactory(date=dt(1999, 2, 2), price=1)
    LendFactory(date=dt(1999, 2, 2), price=6, journal=second_user.journal)

    actual = list(DebtModelService(main_user, "lend").sum_by_month(1999))

    assert actual[0]["date"] == dt(1999, 1, 1)
    assert actual[1]["date"] == dt(1999, 2, 1)


def test_debt_sum_all_not_closed(main_user):
    LendFactory(date=dt(1999, 1, 1), price=12, closed=True)
    LendFactory(date=dt(1999, 1, 1), price=2, returned=1)
    LendFactory(date=dt(1999, 1, 2), price=2, returned=1)
    LendFactory(date=dt(1974, 1, 2), price=3, returned=2)

    expect = {"debt": 7, "debt_return": 4}

    actual = DebtModelService(main_user, "lend").sum_all()

    assert expect == actual


def test_debt_incomes(main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    BorrowFactory(date=dt(1970, 1, 1), account=a1, price=1)
    BorrowFactory(date=dt(1970, 1, 1), account=a1, price=2)
    BorrowFactory(date=dt(1970, 1, 1), account=a2, price=3)
    BorrowFactory(date=dt(1970, 1, 1), account=a2, price=4)

    BorrowFactory(date=dt(1999, 1, 1), account=a1, price=10)
    BorrowFactory(date=dt(1999, 1, 1), account=a1, price=20)
    BorrowFactory(date=dt(1999, 1, 1), account=a2, price=30)
    BorrowFactory(date=dt(1999, 1, 1), account=a2, price=40)

    LendFactory()

    actual = Debt.objects.incomes(main_user)

    assert actual[0]["year"] == 1970
    assert actual[0]["category_id"] == 1
    assert actual[0]["incomes"] == 3

    assert actual[1]["year"] == 1970
    assert actual[1]["category_id"] == 2
    assert actual[1]["incomes"] == 7

    assert actual[2]["year"] == 1999
    assert actual[2]["category_id"] == 1
    assert actual[2]["incomes"] == 30

    assert actual[3]["year"] == 1999
    assert actual[3]["category_id"] == 2
    assert actual[3]["incomes"] == 70


def test_debt_expenses(main_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    LendFactory(date=dt(1970, 1, 1), account=a1, price=1)
    LendFactory(date=dt(1970, 1, 1), account=a1, price=2)
    LendFactory(date=dt(1970, 1, 1), account=a2, price=3)
    LendFactory(date=dt(1970, 1, 1), account=a2, price=4)

    LendFactory(date=dt(1999, 1, 1), account=a1, price=10)
    LendFactory(date=dt(1999, 1, 1), account=a1, price=20)
    LendFactory(date=dt(1999, 1, 1), account=a2, price=30)
    LendFactory(date=dt(1999, 1, 1), account=a2, price=40)

    BorrowFactory()

    actual = Debt.objects.expenses(main_user)

    assert actual[0]["year"] == 1970
    assert actual[0]["category_id"] == 1
    assert actual[0]["expenses"] == 3

    assert actual[1]["year"] == 1970
    assert actual[1]["category_id"] == 2
    assert actual[1]["expenses"] == 7

    assert actual[2]["year"] == 1999
    assert actual[2]["category_id"] == 1
    assert actual[2]["expenses"] == 30

    assert actual[3]["year"] == 1999
    assert actual[3]["category_id"] == 2
    assert actual[3]["expenses"] == 70
