from datetime import date

import freezegun
import pytest

from ..factories import DrinkFactory
from ..lib import views_helper as T


@freezegun.freeze_time('1999-01-03')
@pytest.mark.django_db
def test_dry_days(get_user):
    DrinkFactory()

    actual = T._dry_days(1999)

    assert actual == {'date': date(1999, 1, 1), 'delta': 2}



@pytest.mark.django_db
def test_dry_days_no_records(get_user):
    DrinkFactory()

    actual = T._dry_days(2000)

    assert actual == {}
