import pytest
from django.test import TestCase

from ...core.tests.test_integration_browser import Browser

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class BookkeepingIndex(TestCase, Browser):
    def test_index(self):
        with self.assertNumQueries(29):
            self.browser.get(f"{self.live_server_url}")
