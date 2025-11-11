from datetime import date

import pytest
from django.urls import reverse

from ...accounts.factories import AccountBalance, AccountFactory
from ...accounts.services.model_services import (
    AccountBalanceModelService,
)
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory, SavingTypeFactory
from ...savings.models import SavingBalance
from ...savings.services.model_services import SavingBalanceModelService
from ..factories import SavingChangeFactory, SavingCloseFactory, TransactionFactory
from ..models import SavingChange, SavingClose, Transaction
from ..services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_str():
    t = TransactionFactory.build()

    assert str(t) == "1999-01-01 Account1 -> Account2: 2,00"


def test_transaction_get_absolute_url():
    obj = TransactionFactory()

    assert obj.get_absolute_url() == reverse(
        "transactions:update", kwargs={"pk": obj.pk}
    )


def test_transaction_related(main_user, second_user):
    t1 = AccountFactory(title="T1")
    f1 = AccountFactory(title="F1")

    t2 = AccountFactory(title="T2", journal=second_user.journal)
    f2 = AccountFactory(title="F2", journal=second_user.journal)

    TransactionFactory(to_account=t1, from_account=f1)
    TransactionFactory(to_account=t2, from_account=f2)

    actual = Transaction.objects.related(main_user)

    assert len(actual) == 1
    assert str(actual[0].from_account) == "F1"
    assert str(actual[0].to_account) == "T1"


def test_transaction_items(main_user, second_user):
    t1 = AccountFactory(title="T1")
    f1 = AccountFactory(title="F1")

    t2 = AccountFactory(title="T2", journal=second_user.journal)
    f2 = AccountFactory(title="F2", journal=second_user.journal)

    TransactionFactory(to_account=t1, from_account=f1)
    TransactionFactory(to_account=t2, from_account=f2)

    actual = Transaction.objects.related(main_user)

    assert len(actual) == 1
    assert str(actual[0].from_account) == "F1"
    assert str(actual[0].to_account) == "T1"


def test_transaction_year(main_user, second_user):
    a = AccountFactory(title="T1", journal=second_user.journal)

    TransactionFactory(date=date(1999, 1, 1))
    TransactionFactory(date=date(2000, 1, 1))
    TransactionFactory(date=date(2000, 1, 1), from_account=a)

    actual = TransactionModelService(main_user).year(1999)

    assert actual.count() == 1


def test_transaction_items_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(TransactionModelService(main_user).items())


def test_transaction_year_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(TransactionModelService(main_user).year(1999))


def test_transaction_new_post_save(main_user):
    TransactionFactory()

    assert AccountBalanceModelService(main_user).items().count() == 4

    a1 = AccountBalance.objects.get(account_id=2, year=1999)
    assert a1.account.title == "Account1"
    assert a1.incomes == 0
    assert a1.expenses == 200
    assert a1.balance == -200
    assert a1.delta == 200

    a2 = AccountBalance.objects.get(account_id=1, year=1999)
    assert a2.account.title == "Account2"
    assert a2.incomes == 200
    assert a2.expenses == 0
    assert a2.balance == 200
    assert a2.delta == -200


def test_transaction_update_post_save(main_user):
    a_from = AccountFactory(title="From")
    a_to = AccountFactory(title="To")

    obj = TransactionFactory(
        date=date(1999, 1, 1), from_account=a_from, to_account=a_to, price=100
    )

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.price = 10
    obj_update.save()

    actual = AccountBalanceModelService(main_user).items()

    assert actual.count() == 4

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.incomes == 10
    assert actual.expenses == 0
    assert actual.balance == 10
    assert actual.delta == -10

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.incomes == 0
    assert actual.expenses == 10
    assert actual.balance == -10
    assert actual.delta == 10


def test_transaction_post_save_first_record(main_user):
    a_from = AccountFactory(title="From")
    a_to = AccountFactory(title="To")

    # past records
    IncomeFactory(account=a_from, date=date(1998, 1, 1), price=6)
    ExpenseFactory(account=a_from, date=date(1998, 1, 1), price=5)

    IncomeFactory(account=a_to, date=date(1998, 1, 1), price=5)
    ExpenseFactory(account=a_to, date=date(1998, 1, 1), price=3)

    # truncate AccountBalace
    AccountBalanceModelService(main_user).objects.delete()

    TransactionFactory(
        date=date(1999, 1, 1), from_account=a_from, to_account=a_to, price=1
    )

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 2
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 3
    assert actual.delta == -3

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.past == 1
    assert actual.incomes == 0
    assert actual.expenses == 1
    assert actual.balance == 0
    assert actual.delta == 0

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1998)
    assert actual.account.title == "To"
    assert actual.past == 0
    assert actual.incomes == 5
    assert actual.expenses == 3
    assert actual.balance == 2
    assert actual.delta == -2

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1998)
    assert actual.account.title == "From"
    assert actual.past == 0
    assert actual.incomes == 6
    assert actual.expenses == 5
    assert actual.balance == 1
    assert actual.delta == -1


def test_transaction_post_save_new(main_user):
    main_user.year = 1998

    a_from = AccountFactory(title="From")
    a_to = AccountFactory(title="To")

    # past records
    IncomeFactory(date=date(1998, 1, 1), account=a_from, price=6)
    ExpenseFactory(date=date(1998, 1, 1), account=a_from, price=5)

    IncomeFactory(date=date(1998, 1, 1), account=a_to, price=5)
    ExpenseFactory(date=date(1998, 1, 1), account=a_to, price=3)

    TransactionFactory(
        date=date(1999, 1, 1), from_account=a_from, to_account=a_to, price=1
    )

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 2
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 3
    assert actual.delta == -3

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.past == 1
    assert actual.incomes == 0
    assert actual.expenses == 1
    assert actual.balance == 0
    assert actual.delta == 0


def test_transaction_post_save_update_with_nothing_changed():
    a_from = AccountFactory(title="From")
    a_to = AccountFactory(title="To")

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5


def test_transaction_post_save_change_from_account():
    a_from = AccountFactory(title="From")
    a_from_new = AccountFactory(title="From-New")
    a_to = AccountFactory(title="To")

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)
    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.from_account = a_from_new
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5

    actual = AccountBalance.objects.filter(account_id=a_from.pk, year=1999)
    assert actual.count() == 0

    actual = AccountBalance.objects.get(account_id=a_from_new.pk, year=1999)
    assert actual.account.title == "From-New"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5


def test_transaction_post_save_change_to_account():
    a_from = AccountFactory(title="From")
    a_to = AccountFactory(title="To")
    a_to_new = AccountFactory(title="To-New")

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)

    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5

    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.to_account = a_to_new
    obj_update.save()

    actual = AccountBalance.objects.filter(account_id=a_to.pk, year=1999)
    assert actual.count() == 0

    actual = AccountBalance.objects.get(account_id=a_to_new.pk, year=1999)
    assert actual.account.title == "To-New"
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5

    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5


def test_transaction_post_save_change_from_and_to_account():
    a_from = AccountFactory(title="From")
    a_from_new = AccountFactory(title="From-New")
    a_to = AccountFactory(title="To")
    a_to_new = AccountFactory(title="To-New")

    obj = TransactionFactory(from_account=a_from, to_account=a_to, price=5)

    # from_account
    actual = AccountBalance.objects.get(account_id=a_from.pk, year=1999)
    assert actual.account.title == "From"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5

    # to_account
    actual = AccountBalance.objects.get(account_id=a_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5

    # update from and to
    obj_update = Transaction.objects.get(pk=obj.pk)
    obj_update.to_account = a_to_new
    obj_update.from_account = a_from_new
    obj_update.save()

    # to_account old
    actual = AccountBalance.objects.filter(account_id=a_to.pk, year=1999)
    assert actual.count() == 0

    # to_account new
    actual = AccountBalance.objects.get(account_id=a_to_new.pk, year=1999)
    assert actual.account.title == "To-New"
    assert actual.incomes == 5
    assert actual.expenses == 0
    assert actual.balance == 5

    # from_account old
    actual = AccountBalance.objects.filter(account_id=a_from.pk, year=1999)
    assert actual.count() == 0

    # from_account new
    actual = AccountBalance.objects.get(account_id=a_from_new.pk, year=1999)
    assert actual.account.title == "From-New"
    assert actual.incomes == 0
    assert actual.expenses == 5
    assert actual.balance == -5


def test_transaction_post_delete(main_user):
    obj = TransactionFactory()

    Transaction.objects.get(pk=obj.pk).delete()

    actual = AccountBalanceModelService(main_user).items()

    assert actual.count() == 0
    assert Transaction.objects.all().count() == 0


def test_transaction_post_delete_with_update(main_user):
    TransactionFactory(price=10)

    obj = TransactionFactory()
    Transaction.objects.get(pk=obj.pk).delete()

    assert AccountBalanceModelService(main_user).items().count() == 4

    a1 = AccountBalance.objects.get(account_id=1, year=1999)

    assert a1.account.title == "Account2"
    assert a1.incomes == 10
    assert a1.expenses == 0
    assert a1.balance == 10
    assert a1.delta == -10

    a2 = AccountBalance.objects.get(account_id=2, year=1999)
    assert a2.account.title == "Account1"
    assert a2.incomes == 0
    assert a2.expenses == 10
    assert a2.balance == -10
    assert a2.delta == 10

    assert Transaction.objects.all().count() == 1


def test_transaction_balance_incomes(main_user, transactions):
    actual = Transaction.objects.incomes(main_user)

    # 1974
    assert actual[0]["year"] == 1970
    assert actual[0]["incomes"] == 525
    assert actual[0]["category_id"] == 1

    assert actual[1]["year"] == 1970
    assert actual[1]["incomes"] == 125
    assert actual[1]["category_id"] == 2

    # 1999
    assert actual[2]["year"] == 1999
    assert actual[2]["incomes"] == 325
    assert actual[2]["category_id"] == 1

    assert actual[3]["year"] == 1999
    assert actual[3]["incomes"] == 450
    assert actual[3]["category_id"] == 2


def test_transaction_balance_expenses(main_user, transactions):
    actual = Transaction.objects.expenses(main_user)

    # 1974
    assert actual[0]["year"] == 1970
    assert actual[0]["expenses"] == 125
    assert actual[0]["category_id"] == 1

    assert actual[1]["year"] == 1970
    assert actual[1]["expenses"] == 525
    assert actual[1]["category_id"] == 2

    # 1999
    assert actual[2]["year"] == 1999
    assert actual[2]["expenses"] == 450
    assert actual[2]["category_id"] == 1

    assert actual[3]["year"] == 1999
    assert actual[3]["expenses"] == 325
    assert actual[3]["category_id"] == 2


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_str():
    s = SavingCloseFactory.build()

    assert str(s) == "1999-01-01 Savings From -> Account To: 0,10"


def test_saving_close_get_absolute_url():
    obj = SavingCloseFactory()

    assert obj.get_absolute_url() == reverse(
        "transactions:savings_close_update", kwargs={"pk": obj.pk}
    )


def test_saving_close_related(main_user, second_user):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2", journal=second_user.journal)

    s1 = SavingTypeFactory(title="S1")
    s2 = SavingTypeFactory(title="S2", journal=second_user.journal)

    SavingCloseFactory(to_account=a1, from_account=s1)
    SavingCloseFactory(to_account=a2, from_account=s2)

    actual = SavingClose.objects.related(main_user)

    assert len(actual) == 1
    assert str(actual[0].from_account) == "S1"
    assert str(actual[0].to_account) == "A1"


def test_saving_close_month_sums(main_user, savings_close):
    expect = [{"date": date(1999, 1, 1), "sum": 26, "title": "savings_close"}]

    actual = list(SavingCloseModelService(main_user).sum_by_month(1999))

    assert expect == actual


def test_saving_close_month_sums_only_january(main_user, savings_close):
    expect = [{"date": date(1999, 1, 1), "sum": 26, "title": "savings_close"}]

    actual = list(SavingCloseModelService(main_user).sum_by_month(1999, 1))

    assert expect == actual


def test_saving_close_month_sum_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(SavingCloseModelService(main_user).sum_by_month(1999))


def test_saving_close_post_save(main_user):
    SavingCloseFactory()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert actual[0].account.title == "Account To"
    assert actual[0].past == 0
    assert actual[0].incomes == 10
    assert actual[0].expenses == 0
    assert actual[0].balance == 10

    actual = SavingBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert actual[0].saving_type.title == "Savings From"
    assert actual[0].past_amount == 0
    assert actual[0].past_fee == 0
    assert actual[0].fee == 0
    assert actual[0].incomes == 0


def test_saving_close_post_save_multiple(main_user):
    SavingCloseFactory(price=1, fee=0.5)
    SavingCloseFactory(price=10, fee=5)

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 1
    assert actual[0].saving_type.title == "Savings From"
    assert actual[0].past_amount == 0
    assert actual[0].past_fee == 0
    assert actual[0].fee == 0
    assert actual[0].incomes == 0


def test_saving_close_post_save_update(main_user):
    obj = SavingCloseFactory()

    # update price
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalanceModelService(main_user).year(1999)
    assert actual.count() == 1
    assert actual[0].account.title == "Account To"
    assert actual[0].past == 0
    assert actual[0].incomes == 1
    assert actual[0].expenses == 0
    assert actual[0].balance == 1

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 1
    assert actual[0].saving_type.title == "Savings From"
    assert actual[0].past_amount == 0
    assert actual[0].past_fee == 0
    assert actual[0].fee == 0
    assert actual[0].incomes == 0


def test_saving_close_post_save_first_record():
    _to = AccountFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingFactory(saving_type=_from, price=40, date=date(1998, 1, 1), fee=2)
    IncomeFactory(account=_to, price=10, date=date(1998, 1, 1))

    # truncate table
    SavingBalance.objects.all().delete()
    AccountBalance.objects.all().delete()

    SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 10
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 11

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 40
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 40


def test_saving_close_post_save_new(main_user):
    _to = AccountFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalanceModelService(main_user).year(1999)
    assert actual.count() == 1

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_close_post_save_nothing_changed(main_user):
    _to = AccountFactory(title="To")
    _from = SavingTypeFactory(title="From")

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.save()

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 1

    actual = AccountBalanceModelService(main_user).year(1999)
    assert actual.count() == 1

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_close_post_save_changed_from():
    _to = AccountFactory(title="To")
    _from = SavingTypeFactory(title="From")
    _from_new = SavingTypeFactory(title="From-New")

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)
    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.from_account = _from_new
    obj_update.save()

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    actual = SavingBalance.objects.filter(saving_type_id=_from.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk, year=1999)
    assert actual.saving_type.title == "From-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_close_post_save_changed_to():
    _to = AccountFactory(title="To")
    _to_new = AccountFactory(title="To-New")
    _from = SavingTypeFactory(title="From")

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.save()

    actual = AccountBalance.objects.filter(account_id=_to.pk, year=1999)
    assert actual.count() == 0

    actual = AccountBalance.objects.get(account_id=_to_new.pk, year=1999)
    assert actual.account.title == "To-New"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_close_post_save_changed_from_and_to():
    _to = AccountFactory(title="To")
    _to_new = AccountFactory(title="To-New")
    _from = SavingTypeFactory(title="From")
    _from_new = SavingTypeFactory(title="From-New")

    obj = SavingCloseFactory(to_account=_to, from_account=_from, price=1)

    actual = AccountBalance.objects.get(account_id=_to.pk, year=1999)
    assert actual.account.title == "To"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0

    # update saving change
    obj_update = SavingClose.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.from_account = _from_new
    obj_update.save()

    actual = AccountBalance.objects.filter(account_id=_to.pk, year=1999)
    assert actual.count() == 0

    actual = AccountBalance.objects.get(account_id=_to_new.pk, year=1999)
    assert actual.account.title == "To-New"
    assert actual.past == 0
    assert actual.incomes == 1
    assert actual.expenses == 0
    assert actual.balance == 1

    actual = SavingBalance.objects.filter(saving_type_id=_from.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk, year=1999)
    assert actual.saving_type.title == "From-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_close_post_delete(main_user):
    obj = SavingCloseFactory()

    SavingClose.objects.get(pk=obj.pk).delete()

    actual = AccountBalanceModelService(main_user).year(1999)
    assert actual.count() == 0

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 0
    assert SavingClose.objects.all().count() == 0


def test_saving_close_post_delete_with_update(main_user):
    SavingCloseFactory(price=1, fee=0.5)

    obj = SavingCloseFactory(price=10, fee=5)
    SavingClose.objects.get(pk=obj.pk).delete()

    actual = AccountBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert actual[0].account.title == "Account To"
    assert actual[0].incomes == 1
    assert actual[0].balance == 1

    actual = SavingBalanceModelService(main_user).year(1999)

    assert actual.count() == 1
    assert actual[0].fee == 0
    assert actual[0].incomes == 0

    assert SavingClose.objects.all().count() == 1


def test_saving_close_balance_incomes(main_user, savings_close):
    actual = SavingClose.objects.incomes(main_user)

    # 1974
    assert actual[0]["year"] == 1970
    assert actual[0]["incomes"] == 25
    assert actual[0]["category_id"] == 1

    # 1999
    assert actual[1]["year"] == 1999
    assert actual[1]["incomes"] == 25
    assert actual[1]["category_id"] == 1

    assert actual[2]["year"] == 1999
    assert actual[2]["incomes"] == 1
    assert actual[2]["category_id"] == 2


def test_saving_close_balance_expenses(main_user, savings_close):
    actual = SavingClose.objects.expenses(main_user)

    # 1974
    assert actual[0]["year"] == 1970
    assert actual[0]["expenses"] == 25
    assert actual[0]["fee"] == 5
    assert actual[0]["category_id"] == 1

    # 1999
    assert actual[1]["year"] == 1999
    assert actual[1]["expenses"] == 26
    assert actual[1]["fee"] == 6
    assert actual[1]["category_id"] == 1


# ----------------------------------------------------------------------------
#                                                                 Saving Change
# ----------------------------------------------------------------------------
def test_savings_change_str():
    s = SavingChangeFactory.build()

    assert str(s) == "1999-01-01 Savings From -> Savings To: 0,10"


def test_savings_change_get_absolute_url():
    obj = SavingChangeFactory()

    assert obj.get_absolute_url() == reverse(
        "transactions:savings_change_update", kwargs={"pk": obj.pk}
    )


def test_saving_change_related(main_user, second_user):
    f1 = SavingTypeFactory(title="F1")
    f2 = SavingTypeFactory(title="F2", journal=second_user.journal)

    t1 = SavingTypeFactory(title="T1")
    t2 = SavingTypeFactory(title="T2", journal=second_user.journal)

    SavingChangeFactory(from_account=f1, to_account=t1)
    SavingChangeFactory(from_account=f2, to_account=t2)

    actual = SavingChange.objects.related(main_user)

    assert len(actual) == 1
    assert str(actual[0].from_account) == "F1"
    assert str(actual[0].to_account) == "T1"


def test_saving_change_items_query_count(main_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(SavingChangeModelService(main_user).items())


def test_saving_change_post_save(main_user):
    SavingChangeFactory()

    actual = SavingBalanceModelService(main_user).year(1999)

    assert actual.count() == 2

    assert actual[0].saving_type.title == "Savings From"
    assert actual[0].fee == 0
    assert actual[0].incomes == 0

    assert actual[1].saving_type.title == "Savings To"
    assert actual[1].fee == 0
    assert actual[1].incomes == 10


def test_saving_change_post_save_update(main_user):
    _to = SavingTypeFactory(title="To")
    _from = SavingTypeFactory(title="From")
    obj = SavingChangeFactory(to_account=_to, from_account=_from)

    # update price
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = SavingBalanceModelService(main_user).year(1999)

    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.fee == 0
    assert actual.incomes == 0

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.fee == 0
    assert actual.incomes == 1


def test_saving_change_post_save_first_record(main_user):
    _to = SavingTypeFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingFactory(saving_type=_to, price=50, date=date(1998, 1, 1), fee=2)
    SavingFactory(saving_type=_from, price=40, date=date(1998, 1, 1), fee=2)

    # truncate table
    SavingBalance.objects.all().delete()

    SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 40
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 40

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.past_amount == 50
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 51


def test_saving_change_post_save_new(main_user):
    _to = SavingTypeFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingFactory(saving_type=_to, price=50, date=date(1998, 1, 1), fee=2)
    SavingFactory(saving_type=_from, price=40, date=date(1998, 1, 1), fee=2)

    SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 40
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 40

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.past_amount == 50
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 51


def test_saving_change_post_save_update_nothing_changed(main_user):
    _to = SavingTypeFactory(title="To")
    _from = SavingTypeFactory(title="From")

    SavingFactory(saving_type=_to, price=50, date=date(1998, 1, 1), fee=2)
    SavingFactory(saving_type=_from, price=40, date=date(1998, 1, 1), fee=2)

    # create saving change
    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    # update saving change
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.save()

    actual = SavingBalanceModelService(main_user).year(1999)
    assert actual.count() == 2

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 40
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 40

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.past_amount == 50
    assert actual.past_fee == 2
    assert actual.fee == 2
    assert actual.incomes == 51


def test_saving_change_post_save_changed_from():
    _to = SavingTypeFactory(title="To")
    _from = SavingTypeFactory(title="From")
    _from_new = SavingTypeFactory(title="From-New")

    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.get(saving_type_id=_from, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0

    # update
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.from_account = _from_new
    obj_update.save()

    actual = SavingBalance.objects.filter(saving_type_id=_from.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk, year=1999)
    assert actual.saving_type.title == "From-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 1


def test_saving_change_post_save_changed_to():
    _to = SavingTypeFactory(title="To")
    _to_new = SavingTypeFactory(title="To-New")
    _from = SavingTypeFactory(title="From")

    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 1

    # update
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.save()

    actual = SavingBalance.objects.filter(saving_type_id=_to.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_to_new.pk, year=1999)
    assert actual.saving_type.title == "To-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_change_post_save_changed_to_and_from():
    _to = SavingTypeFactory(title="To")
    _to_new = SavingTypeFactory(title="To-New")
    _from = SavingTypeFactory(title="From")
    _from_new = SavingTypeFactory(title="From-New")

    obj = SavingChangeFactory(to_account=_to, from_account=_from, price=1)

    actual = SavingBalance.objects.get(saving_type_id=_to.pk, year=1999)
    assert actual.saving_type.title == "To"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 1

    actual = SavingBalance.objects.get(saving_type_id=_from.pk, year=1999)
    assert actual.saving_type.title == "From"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0

    # update
    obj_update = SavingChange.objects.get(pk=obj.pk)
    obj_update.to_account = _to_new
    obj_update.from_account = _from_new
    obj_update.save()

    actual = SavingBalance.objects.filter(saving_type_id=_to.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_to_new.pk, year=1999)
    assert actual.saving_type.title == "To-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 1

    actual = SavingBalance.objects.filter(saving_type_id=_from.pk, year=1999)
    assert actual.count() == 0

    actual = SavingBalance.objects.get(saving_type_id=_from_new.pk, year=1999)
    assert actual.saving_type.title == "From-New"
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 0
    assert actual.incomes == 0


def test_saving_change_post_delete(main_user):
    obj = SavingChangeFactory()

    SavingChange.objects.get(pk=obj.pk).delete()

    actual = SavingBalanceModelService(main_user).year(1999)

    assert actual.count() == 0
    assert SavingChange.objects.all().count() == 0


def test_saving_change_post_delete_with_update(main_user):
    SavingChangeFactory(price=1)
    obj = SavingChangeFactory()

    SavingChange.objects.get(pk=obj.pk).delete()

    actual = SavingBalanceModelService(main_user).year(1999)

    assert actual.count() == 2

    assert actual[0].saving_type.title == "Savings From"
    assert actual[0].fee == 0
    assert actual[0].incomes == 0

    assert actual[1].saving_type.title == "Savings To"
    assert actual[1].fee == 0
    assert actual[1].incomes == 1

    assert SavingChange.objects.all().count() == 1
