import pandas as pd
import pytest

from ..lib.get_data import GetObjects as T
from ...incomes.models import Income

pytestmark = pytest.mark.django_db


def test_objects(_incomes_from_db):
    actual = T([Income]).data

    assert 'income' in actual
