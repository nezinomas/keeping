import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlanModelService),
        (IncomePlanModelService),
        (SavingPlanModelService),
        (ExpensePlanModelService),
        (NecessaryPlanModelService),
    ],
)
def test_init_raises_if_no_user(model):
    with pytest.raises(ValueError, match="User required"):
        model(user=None)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlanModelService),
        (IncomePlanModelService),
        (SavingPlanModelService),
        (ExpensePlanModelService),
        (NecessaryPlanModelService),
    ],
)
def test_init_raises_if_anonymous_user(model):
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        model(user=anon)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlanModelService),
        (IncomePlanModelService),
        (SavingPlanModelService),
        (ExpensePlanModelService),
        (NecessaryPlanModelService),
    ],
)
@pytest.mark.django_db
def test_init_succeeds_with_real_user(model, main_user):
    # No need to save — just check __init__
    model(user=main_user)
