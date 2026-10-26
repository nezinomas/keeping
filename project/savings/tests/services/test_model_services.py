from ...services.model_services import SavingTypeModelService


def test_saving_type_model_service_promises_no_year():
    assert not hasattr(SavingTypeModelService, "year")
