from time import sleep

import pytest
from django.test import LiveServerTestCase
from freezegun import freeze_time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ...users.factories import UserFactory
from ..factories import IncomeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Incomes(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.Chrome('../chromedriver')

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()

        UserFactory()
        self.client.login(username='bob', password='123')
        cookie = self.client.cookies['sessionid']

        self.browser.get(self.live_server_url)
        self.browser.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.browser.refresh()


    @freeze_time('1999-1-1')
    def test_search(self):
        IncomeFactory(remark='xxxx')
        IncomeFactory(remark='yyyy')
        IncomeFactory(remark='zzzz')

        self.browser.get(f'{self.live_server_url}/incomes/')

        rows = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr")
        assert len(rows) == 3

        search = self.browser.find_element(by=By.ID, value='id_search')
        search.send_keys('xxxx')
        search.send_keys(Keys.RETURN)

        sleep(0.1)

        rows = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr")
        assert len(rows) == 1 # head row + find row

        cells = self.browser.find_elements(by=By.XPATH, value="//table/tbody/tr[1]/td")
        assert cells[3].text == 'xxxx'
