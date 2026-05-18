import pytest
from unittest.mock import MagicMock
from ...services.index.providers import IndexDataProvider

@pytest.mark.django_db
def test_top_categories_returns_top_5(mocker, main_user):
    # Mock ExpenseModelService to return 7 categories
    mock_expenses = [
        {"title": "Cat 6", "sum": 6000},
        {"title": "Cat 5", "sum": 5000},
        {"title": "Cat 4", "sum": 4000},
        {"title": "Cat 3", "sum": 3000},
        {"title": "Cat 2", "sum": 2000},
        {"title": "Cat 1", "sum": 1000},
        {"title": "Cat 7", "sum": 500},
    ]
    
    mock_service = mocker.patch("project.bookkeeping.services.index.providers.ExpenseModelService")
    mock_service.return_value.sum_by_category.return_value = mock_expenses
    
    provider = IndexDataProvider(main_user)
    data = provider.get_data()
    
    # We expect 'top_categories' to be part of the DTO and have length 5
    assert hasattr(data, "top_categories")
    assert len(data.top_categories) == 5
    # Should be sorted descending by sum
    assert data.top_categories[0]["sum"] == 6000
    assert data.top_categories[-1]["sum"] == 2000

@pytest.mark.django_db
def test_top_categories_empty_data(mocker, main_user):
    mock_service = mocker.patch("project.bookkeeping.services.index.providers.ExpenseModelService")
    mock_service.return_value.sum_by_category.return_value = []
    
    provider = IndexDataProvider(main_user)
    data = provider.get_data()
    
    assert data.top_categories == []
