from types import SimpleNamespace

import pytest


@pytest.fixture(name="types")
def fixture_types():
    return [
        SimpleNamespace(pk=1, closed=None),
        SimpleNamespace(pk=2, closed=None),
    ]
