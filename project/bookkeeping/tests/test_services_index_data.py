import pytest
from ..services.index import IndexServiceData


@pytest.fixture()
def amount_start(mocker):
    mocker.patch(
        'project.bookkeeping.services.index.IndexServiceData.get_amount_start',
        side_effect=[8]
    )


@pytest.fixture()
def data_dummy(mocker):
    mocker.patch(
        'project.bookkeeping.services.index.IndexServiceData.get_data',
        side_effect=[{'foo': 'bar'}]
    )


@pytest.fixture()
def data(mocker):
    module = 'project.bookkeeping.services.index'
    mocker.patch(
        f'{module}.Income.objects.sum_by_month',
        side_effect=['Income sum_by_month data'])
    mocker.patch(
        f'{module}.Expense.objects.sum_by_month',
        side_effect=['Expense sum_by_month data'])
    mocker.patch(
        f'{module}.Saving.objects.sum_by_month',
        side_effect=['Saving sum_by_month data'])
    mocker.patch(
        f'{module}.SavingClose.objects.sum_by_month',
        side_effect=['SavingClose sum_by_month data'])

    debts = [
        [{'date': 'xxxx', 'sum_debt': 2, 'sum_return': 1}],  # borrow
        [{'date': 'xxxx', 'sum_debt': 7, 'sum_return': 5}],  # lend
    ]
    mocker.patch(
        f'{module}.Debt.objects.sum_by_month',
        side_effect=debts)


def test_init(amount_start, data_dummy):
    actual = IndexServiceData(1999)

    assert actual.amount_start == 8
    assert actual.data == {'foo': 'bar'}


def test_get_debt_data(amount_start, data):
    data_ = [
        {'date': 'xxxx-yy-zz', 'sum_debt': 999, 'sum_return': 111}
    ]

    debt, debt_return = IndexServiceData(1111).get_debt_data(data_)

    assert debt == [{'date': 'xxxx-yy-zz', 'sum': 999}]
    assert debt_return == [{'date': 'xxxx-yy-zz', 'sum': 111}]


def test_data(amount_start, data):
    actual = IndexServiceData(1999)

    assert actual.data['incomes'] == 'Income sum_by_month data'
    assert actual.data['expenses'] == 'Expense sum_by_month data'
    assert actual.data['savings'] == 'Saving sum_by_month data'
    assert actual.data['savings_close'] == 'SavingClose sum_by_month data'

    assert actual.data['borrow'] == [{'date': 'xxxx', 'sum': 2}]
    assert actual.data['borrow_return'] == [{'date': 'xxxx', 'sum': 1}]

    assert actual.data['lend'] == [{'date': 'xxxx', 'sum': 7}]
    assert actual.data['lend_return'] == [{'date': 'xxxx', 'sum': 5}]
