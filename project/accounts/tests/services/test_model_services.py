import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import AccountBalanceModelService, AccountModelService

SERVICES = [AccountModelService, AccountBalanceModelService]


@pytest.mark.parametrize("service", SERVICES, ids=["account", "balance"])
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


def test_account_model_service_promises_no_year():
    assert not hasattr(AccountModelService, "year")
