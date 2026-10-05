from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import time_machine

from ...forms import SavingWorthForm
from ...services.model_services import CommonMethodsMixin, SavingWorthModelService
from ..factories import SavingTypeFactory


class DummyMixinService(CommonMethodsMixin):
    """A dummy class just to test the pure mixin methods."""

    pass


def test_common_methods_mixin_items_not_implemented():
    service = DummyMixinService()

    with pytest.raises(NotImplementedError, match="Method items is not implemented."):
        service.items()


def test_common_methods_mixin_promises_no_year():
    assert not hasattr(CommonMethodsMixin, "year")


@pytest.mark.parametrize("picked", ["2000-01-01", "1999-12-31"])
@pytest.mark.parametrize(
    "clock",
    [
        datetime(2000, 1, 1, 0, 30, tzinfo=ZoneInfo("Europe/Vilnius")),
        datetime(1999, 12, 31, 23, 30, tzinfo=ZoneInfo("Europe/Vilnius")),
    ],
)
@pytest.mark.django_db
def test_a_worth_counts_in_the_year_it_was_picked_for(picked, clock, main_user):
    form = SavingWorthForm(
        user=main_user,
        data={"date": picked, "price": "1", "saving_type": SavingTypeFactory().pk},
    )
    with time_machine.travel(clock, tick=False):
        assert form.is_valid()
        form.save()

    actual = SavingWorthModelService(main_user).have()

    assert [x["year"] for x in actual] == [int(picked[:4])]
