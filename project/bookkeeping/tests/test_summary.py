import pandas as pd
import pytest
from mock import Mock

from ...incomes.models import Income
from ..lib.summary import collect_summary_data

pytestmark = pytest.mark.django_db


def test_model_not_exists(incomes):
    actual = collect_summary_data(1999, ['X'])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_model_dont_have_summary_method(incomes):
    model = Mock()
    model.objects.summary.side_effect = Exception('Unknown')
    actual = collect_summary_data(1999, [model])

    assert isinstance(actual, pd.DataFrame)
    assert actual.empty


def test_incomes(incomes):
    actual = collect_summary_data(1999, [Income])

    assert isinstance(actual, pd.DataFrame)

    assert 2 == actual.shape[0]  # rows
    assert 2 == actual.shape[1]  # columns

    assert 'i_past' in actual.columns
    assert 'i_now' in actual.columns

    assert 'Account1' == actual.index.values[0]
    assert 'Account2' == actual.index.values[1]

    assert 5.25 == actual.at['Account1', 'i_past']
    assert 3.25 == actual.at['Account1', 'i_now']

    assert 4.5 == actual.at['Account2', 'i_past']
    assert 3.5 == actual.at['Account2', 'i_now']


def test_incomes_qs_count(incomes, django_assert_max_num_queries):
    with django_assert_max_num_queries(2):
        [*collect_summary_data(1999, [Income])]
