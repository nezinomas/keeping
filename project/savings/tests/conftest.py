import pytest

from ...bookkeeping.tests.helper import quiet_syncs


@pytest.fixture(name="quiet_syncs")
def fixture_quiet_syncs(request):
    if request.node.get_closest_marker("syncs"):
        yield
        return
    with quiet_syncs():
        yield
