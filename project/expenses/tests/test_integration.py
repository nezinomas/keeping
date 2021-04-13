from time import sleep

import pytest
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from ..factories import ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Expenses(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.Chrome('d:/web/chromedriver')

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

    def test_add_one_expense_and_close_modal_form(self):
        self.browser.get('%s%s' % (self.live_server_url, '/expenses/'))

        a = AccountFactory()
        t = ExpenseTypeFactory()
        n = ExpenseNameFactory()

        # click Add Expenses button
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'insert_expense'))
        ).click()

        # select ExpenseType
        s = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "id_expense_type"))))
        s.select_by_value(f'{t.id}')

        # select ExpenseName
        s = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "id_expense_name"))))
        s.select_by_value(f'{n.id}')

        # select Account
        s = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "id_account"))))
        s.select_by_value(f'{a.id}')

        self.browser.find_element_by_id('id_total_sum').send_keys('123.45')
        self.browser.find_element_by_id('add_price').click()

        # click 'Save and Close' button
        self.browser.find_element_by_id('save_close').click()

        # wait while form is closing
        sleep(.5)

        page = self.browser.page_source

        assert t.title in page
        assert n.title in page
        assert '123,45' in page

    def test_empty_required_fields(self):
        self.browser.get('%s%s' % (self.live_server_url, '/expenses/'))

        # click Add Expenses button
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'insert_expense'))
        ).click()

        # click 'Save And Close' button
        WebDriverWait(self.browser, 1).until(
            EC.presence_of_element_located((By.ID, 'save_close'))
        ).click()

        e1 =  WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'error_1_id_expense_type'))
        )
        e2 =  WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'error_1_id_expense_name'))
        )
        e3 =  WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'error_1_id_price'))
        )

        assert e1.text == e2.text == 'Šis laukas yra privalomas.'
        assert e3.text == 'Įsitikinkite, kad reikšmė yra didesnė arba lygi 0.01.'

