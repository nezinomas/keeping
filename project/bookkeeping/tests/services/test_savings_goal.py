import pytest
from mock import MagicMock
from project.bookkeeping.services.index.dtos import IndexDataDTO
from project.bookkeeping.services.index.presenters import IndexContextBuilder
from project.bookkeeping.services.index.providers import IndexDataProvider

def test_savings_goal_in_dto():
    # This should fail if savings_goal is not in DTO
    dto = IndexDataDTO(
        amount_start=100,
        monthly_data=[],
        debts={},
        savings_goal=500.0
    )
    assert dto.savings_goal == 500.0

def test_savings_goal_context_calculation():
    # This should fail if savings_goal_context is missing or incorrect
    mock_balance = MagicMock()
    mock_balance.total_row = {"savings": 250.0}
    
    builder = IndexContextBuilder(balance=mock_balance, savings_goal=500.0)
    actual = builder.savings_goal_context()
    
    assert actual["actual"] == 250.0
    assert actual["target"] == 500.0
    assert actual["percent"] == 50.0

def test_savings_goal_context_zero_target():
    mock_balance = MagicMock()
    mock_balance.total_row = {"savings": 250.0}
    
    builder = IndexContextBuilder(balance=mock_balance, savings_goal=0)
    actual = builder.savings_goal_context()
    
    assert actual["percent"] == 0

@pytest.mark.django_db
def test_index_data_provider_fetches_savings_goal(mocker, main_user):
    # This should fail if providers.py doesn't fetch savings_goal
    mock_plan_service = mocker.patch("project.bookkeeping.services.index.providers.SavingPlanModelService")
    mock_plan_service.return_value.year.return_value.aggregate.return_value = {"price__sum": 1000.0}
    
    provider = IndexDataProvider(main_user)
    data = provider.get_data()
    
    assert data.savings_goal == 1000.0
