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
def data(mocker):
    debts = [
        [{'date': 'xxxx', 'sum_debt': 2, 'sum_return': 1}],  # borrow
        [{'date': 'xxxx', 'sum_debt': 7, 'sum_return': 5}],  # lend
    ]

    module = 'project.bookkeeping.services.index'
    mocker.patch(f'{module}.Debt.objects.sum_by_month', side_effect=debts)
    mocker.patch(f'{module}.Income.objects.sum_by_month', side_effect=['Income sum_by_month data'])
    mocker.patch(f'{module}.Expense.objects.sum_by_month', side_effect=['Expense sum_by_month data'])
    mocker.patch(f'{module}.Saving.objects.sum_by_month', side_effect=['Saving sum_by_month data'])
    mocker.patch(f'{module}.SavingClose.objects.sum_by_month', side_effect=['SavingClose sum_by_month data'])



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


def test_data(amount_start, data):
    I.collect_data(1999)

    assert I.data['incomes'] == 'Income sum_by_month data'
    assert I.data['expenses'] == 'Expense sum_by_month data'
    assert I.data['savings'] == 'Saving sum_by_month data'
    assert I.data['savings_close'] == 'SavingClose sum_by_month data'

    assert I.data['borrow'] == [{'date': 'xxxx', 'sum': 2}]
    assert I.data['borrow_return'] == [{'date': 'xxxx', 'sum': 1}]

    assert I.data['lend'] == [{'date': 'xxxx', 'sum': 7}]
    assert I.data['lend_return'] == [{'date': 'xxxx', 'sum': 5}]
