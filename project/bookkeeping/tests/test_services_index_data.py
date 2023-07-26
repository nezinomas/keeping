import pytest

from ..services.index import IndexServiceData


@pytest.fixture(name="amount_start")
def fixture_amount_start(mocker):
    mocker.patch(
        "project.bookkeeping.services.index.IndexServiceData.get_amount_start",
        side_effect=[8],
    )


@pytest.fixture(name="data_dummy")
def fixture_data_dummy(mocker):
    mocker.patch(
        "project.bookkeeping.services.index.IndexServiceData.get_data",
        side_effect=[{"foo": "bar"}],
    )


@pytest.fixture(name="data")
def fixture_data(mocker):
    module = "project.bookkeeping.services.index"
    mocker.patch(
        f"{module}.Income.objects.sum_by_month",
        side_effect=[{"Income sum_by_month data"}],
    )
    mocker.patch(
        f"{module}.Expense.objects.sum_by_month",
        side_effect=[{"Expense sum_by_month data"}],
    )
    mocker.patch(
        f"{module}.Saving.objects.sum_by_month",
        side_effect=[{"Saving sum_by_month data"}],
    )
    mocker.patch(
        f"{module}.SavingClose.objects.sum_by_month",
        side_effect=[{"SavingClose sum_by_month data"}],
    )

    debts = [
        [{"date": "xxxx", "sum_debt": 2, "sum_return": 1, "title": "debt"}],  # borrow
        [{"date": "xxxx", "sum_debt": 7, "sum_return": 5, "title": "debt"}],  # lend
    ]
    mocker.patch(f"{module}.Debt.objects.sum_by_month", side_effect=debts)


def test_init(amount_start, data_dummy):
    actual = IndexServiceData(1999)

    assert actual.amount_start == 8
    assert actual.data == {"foo": "bar"}


def test_get_debt_data(amount_start, data):
    _data = [
        {"date": "xxxx-yy-zz", "sum_debt": 999, "sum_return": 111, "title": "debt"}
    ]

    debt = IndexServiceData(1111).split_debt_data(_data)

    assert debt[0] == {"date": "xxxx-yy-zz", "sum": 999, "title": "debt"}
    assert debt[1] == {"date": "xxxx-yy-zz", "sum": 111, "title": "debt_return"}


def test_data(amount_start, data):
    actual = IndexServiceData(1999).data

    assert actual == [
        "Income sum_by_month data",
        "Expense sum_by_month data",
        "Saving sum_by_month data",
        "SavingClose sum_by_month data",
        {"date": "xxxx", "sum": 2, "title": "debt"},
        {"date": "xxxx", "sum": 1, "title": "debt_return"},
        {"date": "xxxx", "sum": 7, "title": "debt"},
        {"date": "xxxx", "sum": 5, "title": "debt_return"},
    ]
