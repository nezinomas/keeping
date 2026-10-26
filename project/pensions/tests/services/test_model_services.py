from ...services.model_services import PensionTypeModelService


def test_pension_type_model_service_promises_no_year():
    assert not hasattr(PensionTypeModelService, "year")
