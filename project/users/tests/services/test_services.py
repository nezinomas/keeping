import pytest

from ...services.model_services import UserModelService


def test_user_model_service_year_not_implemented(mocker):
    mock_user = mocker.Mock()
    service = UserModelService(mock_user)

    with pytest.raises(NotImplementedError, match="Method year is not implemented."):
        service.year(2026)


def test_user_model_service_items_not_implemented(mocker):
    mock_user = mocker.Mock()
    service = UserModelService(mock_user)

    with pytest.raises(NotImplementedError, match="Method items is not implemented."):
        service.items()
