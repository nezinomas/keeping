import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import DebtModelService, DebtReturnModelService


@pytest.mark.parametrize(
    "service",
    [DebtModelService, DebtReturnModelService],
    ids=["debt", "debt_return"],
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
        service(user=user, debt_type="X")
