import pytest

from ...services.model_services import PensionTypeModelService


def test_pension_type_model_service_promises_no_year():
    assert not hasattr(PensionTypeModelService, "year")


@pytest.mark.django_db
def test_pension_funds_do_not_join_the_journal(main_user):
    sql = str(PensionTypeModelService(main_user).items().query)

    assert "journals_journal" not in sql
