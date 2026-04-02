from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from mock import Mock

from ....expenses.models import Expense
from ....expenses.tests.factories import ExpenseFactory
from ...mixins import queryset, views


@pytest.mark.xfail
def test_queryset_fail():
    class Dummy(queryset.GetQuerysetMixin):
        model = SimpleNamespace(objects=SimpleNamespace())

    Dummy().get_queryset()


def test_queryset_retun_qs():
    class Dummy(queryset.GetQuerysetMixin):
        model = SimpleNamespace(
            _meta=SimpleNamespace(verbose_name="ModelName"),
            objects=SimpleNamespace(related=lambda user: "xxx"),
        )
        request = Mock()

    actual = Dummy().get_queryset()

    assert actual == "xxx"


def test_queryset_raises_improperly_configured():
    class Dummy(queryset.GetQuerysetMixin):
        model = None
        request = Mock()

    with pytest.raises(ImproperlyConfigured) as exc:
        Dummy().get_queryset()

    assert "Dummy is missing a model definition. Define Dummy.model." in str(exc.value)


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
