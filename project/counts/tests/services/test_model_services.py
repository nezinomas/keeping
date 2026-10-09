import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import CountModelService, CountTypeModelService


@pytest.mark.parametrize(
    "service",
    [
        pytest.param(CountModelService, id="count"),
        pytest.param(CountTypeModelService, id="count_type"),
    ],
)
@pytest.mark.parametrize(
    "user, message",
    [
        pytest.param(None, "User required", id="no_user"),
        pytest.param(
            AnonymousUser(), "Authenticated user required", id="anonymous_user"
        ),
    ],
)
def test_init_raises_without_a_real_user(service, user, message):
    with pytest.raises(ValueError, match=message):
        service(user=user)


def test_count_type_model_service_promises_no_year():
    assert not hasattr(CountTypeModelService, "year")
