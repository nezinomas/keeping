import pytest

from ....core.tests.utils import view_for
from ...models import Debt
from ...views import DebtLists, DebtReturnLists

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "view_class",
    [DebtLists, DebtReturnLists],
    ids=["debt_lists", "debt_return_lists"],
)
def test_a_user_with_no_year_raises(main_user, rf, view_class):
    main_user.year = None
    view = view_for(rf, main_user, view_class, debt_type=Debt.DebtType.BORROW)

    with pytest.raises(ValueError, match="has no year"):
        view.get_queryset()
