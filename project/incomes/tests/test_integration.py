from time import sleep

import pytest
import time_machine
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..factories import IncomeFactory
from ...core.tests.utils import Browser

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Incomes(Browser):
    @time_machine.travel("1999-1-1")
    def test_search(self):
        IncomeFactory(remark="xxxx")
        IncomeFactory(remark="yyyy")
        IncomeFactory(remark="zzzz")

        self.browser.get(f"{self.live_server_url}/incomes/")

        rows = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr")
        assert len(rows) == 3

        search = self.browser.find_element(by=By.ID, value="id_search")
        search.send_keys("xxxx")
        search.send_keys(Keys.RETURN)

        sleep(0.1)

        rows = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr")
        assert len(rows) == 1  # head row + find row

        cells = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr[1]/td")
        assert cells[3].text == "xxxx"
