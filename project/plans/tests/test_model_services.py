import pytest
from django.contrib.auth.models import AnonymousUser

from ..models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan
from ..services.model_services import ModelService


@pytest.mark.parametrize(
    "model",
    [
        (DayPlan),
        (IncomePlan),
        (SavingPlan),
        (ExpensePlan),
        (NecessaryPlan),
    ],
)
def test_init_raises_if_no_user(model):
    with pytest.raises(ValueError, match="User required"):
        ModelService(model, user=None)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlan),
        (IncomePlan),
        (SavingPlan),
        (ExpensePlan),
        (NecessaryPlan),
    ],
)
def test_init_raises_if_anonymous_user(model):
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        ModelService(model, user=anon)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlan),
        (IncomePlan),
        (SavingPlan),
        (ExpensePlan),
        (NecessaryPlan),
    ],
)
@pytest.mark.django_db
def test_init_succeeds_with_real_user(model, main_user):
    # No need to save — just check __init__
    ModelService(model, user=main_user)
