from datetime import date

import pytest

from ...core.tests.utils import view_for
from ..services.counter_life import CounterLife
from ..views import TabData

pytestmark = pytest.mark.django_db


def _data_tab(rf, user):
    return view_for(rf, user, TabData, slug="x", tab="data")


def _records_of(rf, user):
    return _data_tab(rf, user).get_queryset()


def _notice_year_of(rf, user):
    view = _data_tab(rf, user)
    # get() sets it from get_queryset(), which raises first
    view.object_list = []
    return view.get_context_data()


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(
            lambda rf, user: CounterLife.read(user, "x", date(1999, 1, 1)),
            id="counter_life",
        ),
        pytest.param(_records_of, id="data_tab_records"),
        pytest.param(_notice_year_of, id="data_tab_notice_year"),
    ],
)
def test_a_user_with_no_year_raises(main_user, rf, read):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        read(rf, main_user)
