from ...services.model_services import CountTypeModelService


def test_count_type_model_service_promises_no_year():
    assert not hasattr(CountTypeModelService, "year")
