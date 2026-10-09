import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
    SavingTypeModelService,
)


@pytest.mark.parametrize(
    "service",
    [SavingModelService, SavingTypeModelService, SavingBalanceModelService],
    ids=["saving", "saving_type", "saving_balance"],
)
@pytest.mark.parametrize(
    "user, message",
    [
        (None, "User required"),
        (AnonymousUser(), "Authenticated user required"),
    ],
    ids=["no_user", "anonymous_user"],
)
def test_init_raises_without_a_real_user(service, user, message):
    with pytest.raises(ValueError, match=message):
        service(user=user)


def test_saving_type_model_service_promises_no_year():
    assert not hasattr(SavingTypeModelService, "year")
