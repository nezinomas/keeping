from time import sleep

import pytest
from django.test import LiveServerTestCase
from freezegun import freeze_time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.webtest
class Expenses(LiveServerTestCase):
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

    def test_add_two_expenses(self):
        self.browser.get('%s%s' % (self.live_server_url, '/expenses/'))

        a = AccountFactory()
        t = ExpenseTypeFactory()
        n = ExpenseNameFactory()
        t1 = ExpenseTypeFactory(title='Expense Type 1')
        n1 = ExpenseNameFactory(title='Expense Name 1', parent=t1)

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

        # click Insert button
        self.browser.find_element_by_id('submit').click()
        sleep(.5)

        # ----------------------------- Second expense
        # select ExpenseType
        s = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "id_expense_type"))))
        s.select_by_value(f'{t1.id}')

        # select ExpenseName
        s = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "id_expense_name"))))
        s.select_by_value(f'{n1.id}')

        # select Account
        s = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "id_account"))))
        s.select_by_value(f'{a.id}')

        self.browser.find_element_by_id('id_total_sum').send_keys('65.78')
        self.browser.find_element_by_id('add_price').click()

        # click Insert button
        self.browser.find_element_by_id('save_close').click()
        sleep(.5)

        page = self.browser.page_source

        assert t.title in page
        assert n.title in page
        assert '123,45' in page

        assert t1.title in page
        assert n1.title in page
        assert '65,78' in page

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

    @freeze_time('1999-1-1')
    def test_search(self):
        ExpenseFactory(remark='xxxx')
        ExpenseFactory(remark='yyyy')
        ExpenseFactory(remark='zzzz')

        self.browser.get('%s%s' % (self.live_server_url, '/expenses/'))

        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, 'id_search'))
        ).send_keys('xxxx')

        self.browser.find_element_by_id('search_btn').click()

        sleep(0.5)

        rows = self.browser.find_elements_by_xpath("//table/tbody/tr")
        assert len(rows) == 1 # head row + find row

        cells = self.browser.find_elements_by_xpath("//table/tbody/tr[1]/td")
        assert cells[5].text == 'xxxx'
