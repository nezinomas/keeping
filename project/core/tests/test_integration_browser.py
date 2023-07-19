from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from ...users.factories import UserFactory


class Browser(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        options = webdriver.ChromeOptions()
        cls.browser = webdriver.Chrome(service=Service('../chromedriver.exe'), options=options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()

        UserFactory()
        self.client.login(username="bob", password="123")
        cookie = self.client.cookies["sessionid"]

        self.browser.get(self.live_server_url)
        self.browser.add_cookie(
            {"name": "sessionid", "value": cookie.value, "secure": False, "path": "/"}
        )
        self.browser.refresh()
