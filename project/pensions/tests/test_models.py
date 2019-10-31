from datetime import date, datetime
from decimal import Decimal

import pytest

from ..factories import PensionFactory, PensionTypeFactory
from ..models import Pension, PensionType

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  PensionType
# ----------------------------------------------------------------------------
def test_type_str():
    p = PensionTypeFactory.build()

    assert 'PensionType' == str(p)


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_str():
    p = PensionFactory.build()

    assert '1999-01-01: PensionType' == str(p)


def test_pension_items(pensions):
    assert 4 == len(Pension.objects.items())


def test_pension_items_query_count(django_assert_max_num_queries, pensions):
    with django_assert_max_num_queries(1):
        qs = Pension.objects.items()
        for r in qs:
            _ = r.pension_type.title


def test_pension_year(pensions):
    assert 2 == len(Pension.objects.year(1999))


def test_pension_year_query_count(django_assert_max_num_queries, pensions):
    with django_assert_max_num_queries(1):
        qs = Pension.objects.year(1999)
        for r in qs:
            _ = r.pension_type.title


def test_pension_summary_query_count(django_assert_max_num_queries, pensions):
    with django_assert_max_num_queries(1):
        qs = Pension.objects.summary(1999)
        for r in qs:
            _ = r['title'].lower()


def test_pension_summary(pensions):
    expect = [{
        'id': 1,
        'title': 'PensionType',
        's_past': Decimal(3.5),
        's_now': Decimal(4.5),

    }]

    actual = list(Pension.objects.summary(1999))

    assert expect == actual
