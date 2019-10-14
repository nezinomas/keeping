import pytest

from ..models import Profile
from ...core.factories import ProfileFactory


def test_profile_str():
    p = ProfileFactory.build()

    assert 'bob' == str(p)
