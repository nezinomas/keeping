from mock import patch
import pytest
from ..services.index import IndexServiceData as I


@pytest.fixture()
def amount_start(monkeypatch):
    monkeypatch.setattr(
        'project.bookkeeping.services.index.IndexServiceData.get_amount_start',
        lambda x, y: 8
    )


@pytest.fixture()
def data_dummy(monkeypatch):
    monkeypatch.setattr(
        'project.bookkeeping.services.index.IndexServiceData.get_data',
        lambda x, y: {'foo': 'bar'}
    )


@pytest.fixture()
def data(monkeypatch):
    monkeypatch.setattr(
        'project.bookkeeping.services.index.Debt.objects.sum_by_month',
        lambda x, debt_type: [{'date': 'xxxx', 'sum_debt': 2, 'sum_return': 1}])


def test_init(amount_start, data_dummy):
    I.collect_data(1999)

    assert I.amount_start == 8
    assert I.data == {'foo': 'bar'}


def test_get_debt_data():
    data = [
        {'date': 'xxxx-yy-zz', 'sum_debt': 999, 'sum_return': 111}
    ]

    debt, debt_return = I.get_debt_data(data)

    assert debt == [{'date': 'xxxx-yy-zz', 'sum': 999}]
    assert debt_return == [{'date': 'xxxx-yy-zz', 'sum': 111}]
