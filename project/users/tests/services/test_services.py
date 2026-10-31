from ...services.model_services import UserModelService


def test_user_model_service_promises_no_year():
    assert not hasattr(UserModelService, "year")
