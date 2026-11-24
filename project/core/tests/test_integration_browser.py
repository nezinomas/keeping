from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from ...users.tests.factories import UserFactory

INK = "rgb(22, 34, 43)"  # --skin-ink
INK_MUTED = "rgb(90, 106, 117)"  # --skin-ink-muted
INK_FAINT = "rgb(139, 151, 159)"  # --skin-ink-faint
GAIN = "rgb(31, 107, 74)"  # --skin-gain
HARM = "rgb(125, 39, 51)"  # --skin-harm
# a tip's bubble is a ::before, with no rect: a point in a drawn one answers with
# its .tip, every fourth pixel to find it and each pixel of its rim for its edges
FIND_TIP = "const tip = document.querySelector(arguments[0]);"
TIP_BOX = (
    FIND_TIP
    + """
    const own = tip.getBoundingClientRect();
    const drawn = (x, y) => document.elementFromPoint(x, y) === tip
        && !(x >= own.left - 1 && x <= own.right + 1
            && y >= own.top - 1 && y <= own.bottom + 1);
    let at = null;
    const grow = (x, y) => {
        at ??= {left: x, top: y, right: x + 1, bottom: y + 1};
        at.left = Math.min(at.left, x); at.right = Math.max(at.right, x + 1);
        at.top = Math.min(at.top, y); at.bottom = Math.max(at.bottom, y + 1);
    };
    for (let y = 0; y < innerHeight; y += 4) {
        for (let x = 0; x < innerWidth; x += 4) if (drawn(x, y)) grow(x, y);
    }
    const found = {...at};
    for (let y = found.top - 4; at && y < found.bottom + 4; y++) {
        for (let x = found.left - 4; x < found.right + 4; x++) {
            const inside = x > found.left && x < found.right - 1
                && y > found.top && y < found.bottom - 1;
            if (!inside && drawn(x, y)) grow(x, y);
        }
    }
    const bubble = getComputedStyle(tip, '::before');
    const [width, height] = [bubble.width, bubble.height].map(parseFloat);
    const lines = (height - parseFloat(bubble.paddingTop)
        - parseFloat(bubble.paddingBottom)) / parseFloat(bubble.lineHeight);
"""
)
# the bundle as a browser without anchor positioning reads it: the anchored rules
# gone, the `@supports not` ones lifted out of their query. Returns the queries met
NO_ANCHORING = """
    let met = 0;
    const unanchor = (parent) => {
        for (let i = parent.cssRules.length - 1; i >= 0; i--) {
            const rule = parent.cssRules[i];
            const query = rule instanceof CSSSupportsRule ? rule.conditionText : '';
            if (!query.includes('anchor-scope')) {
                if (rule.cssRules) unanchor(rule);
                continue;
            }
            const lifted = [...rule.cssRules].map(inner => inner.cssText).reverse();
            parent.deleteRule(i);
            if (query.startsWith('not')) {
                lifted.forEach(text => parent.insertRule(text, i));
            }
            met++;
        }
    };
    [...document.styleSheets]
        .filter(sheet => (sheet.href || '').includes('paper.min.css'))
        .forEach(unanchor);
    return met;
"""


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
        # a cleanup, not tearDownClass: it runs even when the lines below raise
        cls.addClassCleanup(cls.browser.quit)
        # minimized, so a run never takes the desktop; the emulation keeps the page
        # focused, or :focus-within stops matching when another window has focus
        cls.browser.minimize_window()
        cls.browser.execute_cdp_cmd(
            "Emulation.setFocusEmulationEnabled", {"enabled": True}
        )

    def setUp(self):
        super().setUp()

        UserFactory()
        self.client.login(username="bob", password="123")
        cookie = self.client.cookies["sessionid"]

        self.browser.get(self.live_server_url)
        self.browser.add_cookie(
            {"name": "sessionid", "value": cookie.value, "secure": False, "path": "/"}
        )
        # each test starts logged in on the index; not refresh(), which reloads the
        # login the first get was sent to before the cookie existed
        self.browser.get(self.live_server_url)
        self.wait_until_idle()

    def wait_until_idle(self, timeout=10):
        # no query here mid-request: the test and the live server share one sqlite
        # connection; a streak, since a swap starts the next load-triggered requests
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

    def wait_two_frames(self):
        # a scroll's fade or Alpine's x-show lands a frame after what set it off
        self.browser.execute_async_script(
            "requestAnimationFrame(() => requestAnimationFrame(arguments[0]));"
        )

    def open_at(self, path: str, width: int):
        self.addCleanup(
            self.browser.execute_cdp_cmd, "Emulation.clearDeviceMetricsOverride", {}
        )
        self.browser.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        self.open(path)

    def open(self, path: str):
        self.browser.get(f"{self.live_server_url}{path}")
        self.wait_until_idle()

    def click_tab(self, name: str):
        self.browser.find_element(By.ID, f"tab-{name}").click()
        self.wait_until_idle()

    def read_chart(self, container: str, body: str, *args):
        # `body` reads `c`, the chart in `container`; its own arguments start at [1]
        return self.browser.execute_script(
            "const c = Highcharts.charts.find(c => c"
            "  && c.renderTo.id === arguments[0] && c.renderTo.isConnected);" + body,
            container,
            *args,
        )

    def assert_overview_chart_redraws(self, path: str, container: str):
        self.open(path)
        assert self._chart_drawn_in(container), "no chart on load"

        for tab in ("data", "index"):
            self.click_tab(tab)

        assert self._chart_drawn_in(container), "no chart after a tab swap"

    def listed_rows(self, columns: tuple[str, ...]) -> list[dict[str, str]]:
        return [
            dict(zip(columns, [td.text for td in tr.find_elements(By.TAG_NAME, "td")]))
            for tr in self.browser.find_elements(By.CSS_SELECTOR, "#data tbody tr")
        ]

    def _chart_drawn_in(self, container: str) -> bool:
        return bool(
            self.browser.find_elements(
                By.CSS_SELECTOR, f"#{container} svg.highcharts-root"
            )
        )
