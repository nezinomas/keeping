from datetime import date

import pytest

from ..context import context_months, yday
from ..lib.date import set_date_with_user_year

pytestmark = pytest.mark.django_db


def _request(rf, user):
    request = rf.get("/")
    request.user = user
    return request


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(lambda rf, user: yday(_request(rf, user)), id="yday_processor"),
        pytest.param(
            lambda rf, user: context_months(_request(rf, user)),
            id="context_months_processor",
        ),
        pytest.param(
            lambda rf, user: set_date_with_user_year(user, date(1999, 1, 1)),
            id="set_date_with_user_year",
        ),
    ],
)
def test_a_user_with_no_year_raises(main_user, rf, read):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        read(rf, main_user)
