from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from ...users.tests.factories import UserFactory


class Browser(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        chrome_options = ChromeOptions()
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        cls.browser = webdriver.Chrome(
            options=chrome_options,
            service=ChromeService(ChromeDriverManager().install()),
        )

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
        self.wait_until_idle()

    def wait_until_idle(self, timeout=10):
        # The test thread and the live server share one in-memory sqlite
        # connection, so a query here during a request wedges both. A streak,
        # because a swap starts the next wave of load-triggered requests.
        quiet = 0

        def settled(browser):
            nonlocal quiet
            idle = browser.execute_script(
                "return document.readyState === 'complete'"
                " && !document.querySelector('.htmx-request')"
            )
            quiet = quiet + 1 if idle else 0
            return quiet == 3

        WebDriverWait(self.browser, timeout, poll_frequency=0.1).until(settled)

    def assert_overview_chart_redraws(self, path: str, container: str):
        self.browser.get(f"{self.live_server_url}{path}")
        self.wait_until_idle()
        assert self._chart_drawn_in(container), "no chart on load"

        for tab in ("data", "index"):
            self.browser.find_element(By.ID, f"tab-{tab}").click()
            self.wait_until_idle()

        assert self._chart_drawn_in(container), "no chart after a tab swap"

    def _chart_drawn_in(self, container: str) -> bool:
        return bool(
            self.browser.find_elements(
                By.CSS_SELECTOR, f"#{container} svg.highcharts-root"
            )
        )
