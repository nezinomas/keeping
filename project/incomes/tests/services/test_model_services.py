import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import IncomeModelService, IncomeTypeModelService


@pytest.mark.parametrize(
    "service",
    [IncomeModelService, IncomeTypeModelService],
    ids=["income", "income_type"],
)
@pytest.mark.parametrize(
    "user, message",
    [(None, "User required"), (AnonymousUser(), "Authenticated user required")],
    ids=["no_user", "anonymous_user"],
)
def test_init_raises_without_a_real_user(service, user, message):
    with pytest.raises(ValueError, match=message):
        service(user=user)


def test_income_type_model_service_promises_no_year():
    assert not hasattr(IncomeTypeModelService, "year")
