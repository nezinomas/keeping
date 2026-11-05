import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from ...core.tests.test_integration_browser import Browser
from .factories import TransactionFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Transactions(Browser):
    def test_a_tab_opened_by_url_pins_its_table_head(self):
        TransactionFactory()

        self.open_at(reverse("transactions:tab_transactions"), 1280)

        assert self.browser.find_elements(
            By.CSS_SELECTOR, ".sticky-table thead.tableFloatingHeaderOriginal"
        )
