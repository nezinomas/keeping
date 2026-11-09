import pytest

from ...core.tests.utils import view_for
from ..models import CountType
from ..views import TabData, TabIndex

pytestmark = pytest.mark.django_db


def _data_tab(rf, user):
    return view_for(rf, user, TabData, slug="x", tab="data")


def _records_of(rf, user):
    return _data_tab(rf, user).get_queryset()


def _index_tab(rf, user):
    view = view_for(rf, user, TabIndex, slug="x")
    view.object = CountType(slug="x")
    return view.get_context_data()


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(_index_tab, id="index_tab"),
        pytest.param(_records_of, id="data_tab_records"),
    ],
)
def test_a_user_with_no_year_raises(main_user, rf, read):
    main_user.year = None

    with pytest.raises(ValueError, match="has no year"):
        read(rf, main_user)
