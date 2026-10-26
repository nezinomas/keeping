from ...services.model_services import IncomeTypeModelService


def test_income_type_model_service_promises_no_year():
    assert not hasattr(IncomeTypeModelService, "year")
