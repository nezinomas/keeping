import pytest

from ....expenses.models import Expense
from ....expenses.tests.factories import ExpenseFactory
from ...mixins import views


def test_search_mixin_no_query():
    class Dummy(views.SearchViewMixin):
        search_method = "search_expenses"

    assert Dummy().search_statistic(None) == {}


def test_search_mixin_wrong_search_method():
    class Dummy(views.SearchViewMixin):
        search_method = "x"

    assert Dummy().search_statistic(None) == {}


@pytest.mark.django_db
def test_search_mixin_with_sql_wrong_search_method():
    ExpenseFactory()
    sql = Expense.objects.all()

    class Dummy(views.SearchViewMixin):
        search_method = "x"

    assert Dummy().search_statistic(sql) == {}


@pytest.mark.django_db
def test_search_mixin_with_sql():
    ExpenseFactory()
    ExpenseFactory()

    sql = Expense.objects.all()

    class Dummy(views.SearchViewMixin):
        search_method = "search_expenses"

    actual = Dummy().search_statistic(sql)

    assert actual == {"count": 2, "sum_price": 224, "sum_quantity": 26, "average": 8.0}
