from contextlib import nullcontext

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import BaseModelService, DatedModelService


class Undated(BaseModelService):
    def get_queryset(self):
        return []

    def items(self):
        return []


class DatedWithoutYear(DatedModelService):
    def get_queryset(self):
        return []

    def items(self):
        return []


REAL_USER = get_user_model()(username="real")


@pytest.mark.parametrize(
    "user, refusal",
    [
        pytest.param(
            None, pytest.raises(ValueError, match="User required"), id="no_user"
        ),
        pytest.param(
            AnonymousUser(),
            pytest.raises(ValueError, match="Authenticated user required"),
            id="anonymous_user",
        ),
        pytest.param(REAL_USER, nullcontext(), id="real_user"),
    ],
)
def test_a_service_serves_only_a_real_user(user, refusal):
    with refusal:
        assert Undated(user).user is REAL_USER


def test_a_dated_service_must_say_how_it_reads_a_year(main_user):
    with pytest.raises(TypeError, match="year"):
        DatedWithoutYear(main_user)
