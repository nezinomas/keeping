from time import sleep

import pytest
from django.test import LiveServerTestCase
from freezegun import freeze_time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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

        self.browser.get('%s%s' % (self.live_server_url, '/incomes/'))

        rows = self.browser.find_elements_by_xpath("//table/tbody/tr")
        assert len(rows) == 3

        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'id_search'))
        ).send_keys('xxxx')

        self.browser.find_element_by_id('search_btn').click()

        sleep(0.5)

        rows = self.browser.find_elements_by_xpath("//table/tbody/tr")
        assert len(rows) == 1 # head row + find row

        cells = self.browser.find_elements_by_xpath("//table/tbody/tr[1]/td")
        assert cells[3].text == 'xxxx'
