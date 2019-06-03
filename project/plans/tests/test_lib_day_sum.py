import pytest
import pandas as pd

from ..lib.day_sum import DaySum


def expense_plans():
    data = {

    }
    return pd.DataFrame(data)


@pytest.fixture(autouse=True)
def mock_get_expense_plans(monkeypatch, request):
    monkeypatch.setattr(DaySum, '_DaySum_get_expense_plans', lambda x: expense_plans())
