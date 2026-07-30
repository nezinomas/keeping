import pytest
import time_machine
from django.utils.translation import gettext as _

from ....core.lib.date import years
from ...services import history

pytestmark = pytest.mark.django_db


@time_machine.travel("2000-01-01")
def test_load_service_all_years(main_user):
    actual = history.load_service(main_user)

    assert actual["all_years"] == len(years())


@time_machine.travel("2000-01-01")
def test_years(main_user):
    qs = [{"year": 1998, "qty": 1, "stdav": 2.5}]
    actual = history.HistoryService(main_user, qs).years

    assert actual == [1998, 1999, 2000]


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 1, 2.5, [0.025, 0.0]),
        ("wine", 1, 8, [0.08, 0.0]),
        ("vodka", 1, 40, [0.4, 0.0]),
        ("stdav", 1, 10, [0.1, 0.0]),
    ],
)
@time_machine.travel("2000-01-01")
def test_pure_alcohol(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(main_user, qs).alcohol

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, unit, decimals",
    [
        ("beer", "ml", 0),
        ("wine", "ml", 0),
        ("vodka", "ml", 0),
        ("stdav", "Std Av", 1),
    ],
)
@time_machine.travel("2000-01-01")
def test_chart_is_labelled_in_the_selected_unit(drink_type, unit, decimals, main_user):
    """A Std Av day is shown as typed, so the chart cannot claim millilitres."""
    main_user.drink_type = drink_type

    chart = history.load_service(main_user)["chart"]

    assert chart["unit"] == unit
    assert chart["decimals"] == decimals
    assert chart["text"]["per_day"] == f"{_('Average per day')}, {unit}"


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [500.0, 0.0]),
        ("wine", 365, 2_920, [750.0, 0.0]),
        ("vodka", 365, 14_600, [1000.0, 0.0]),
        # 365 Std Av over 365 days is 1 a day — not the 10 ml of alcohol in it
        ("stdav", 365, 365, [1.0, 0.0]),
    ],
)
@time_machine.travel("2000-01-01")
def test_per_day(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(main_user, qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [500.0, 182_500]),
        ("wine", 365, 2_920, [750.0, 273_750]),
        ("vodka", 365, 14_600, [1000.0, 365_000]),
        ("stdav", 365, 365, [1.0, 365]),
    ],
)
@time_machine.travel("2000-01-01")
def test_per_day_adjusted_for_current_year(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [
        {"year": 1999, "qty": qty, "stdav": stdav},
        {"year": 2000, "qty": qty, "stdav": stdav},
    ]

    actual = history.HistoryService(main_user, qs).per_day

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [365.0, 0.0]),
        ("wine", 365, 2_920, [365.0, 0.0]),
        ("vodka", 365, 14_600, [365.0, 0.0]),
        ("stdav", 365, 365, [365.0, 0.0]),
    ],
)
@time_machine.travel("2000-01-01")
def test_quantity(drink_type, qty, stdav, expect, main_user):
    main_user.drink_type = drink_type

    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(main_user, qs).quantity

    assert actual == expect
