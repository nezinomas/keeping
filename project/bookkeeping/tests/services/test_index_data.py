import pytest

from ...services.index import IndexServiceData


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
    mocker.patch(
        "project.bookkeeping.services.index.IndexServiceData.get_debts",
        side_effect=[{"foo1": "bar1"}],
    )


def test_init(main_user, amount_start, data_dummy):
    actual = IndexServiceData(main_user)

    assert actual.amount_start == 8
    assert actual.data == {"foo": "bar"}
    assert actual.debts == {"foo1": "bar1"}
