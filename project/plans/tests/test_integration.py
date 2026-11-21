import pytest
from django.urls import reverse

from ...core.tests.test_integration_browser import (
    FIND_TIP,
    INK_MUTED,
    NO_ANCHORING,
    TIP_BOX,
    Browser,
)

pytestmark = pytest.mark.django_db

HINT = "#necessary-expense-plans .panel__hint"
# where the hint's bubble lies: 8px under its `?`, inside the window, and whether
# it spans its Panel's title
HINT_PLACED = (
    TIP_BOX
    + """
    const title = tip.closest('.panel__title').getBoundingClientRect();
    return {
        position: bubble.position,
        width: Math.round(width),
        gap_is_8px: !!at && Math.abs(at.top - own.bottom - 8) < 2,
        in_the_window: !!at && at.left >= 0 && at.right <= innerWidth,
        spans_its_title: !!at && Math.abs(at.left - title.left) < 2
            && Math.abs(at.right - title.right) < 2,
    };
"""
)


@pytest.mark.webtest
class Plans(Browser):
    def test_a_phone_opens_the_hint_under_it_with_and_without_anchoring(self):
        self.open_at(reverse("plans:tab_expenses"), 360)
        title = self.browser.execute_script(
            FIND_TIP + " return Math.round("
            "  tip.closest('.panel__title').getBoundingClientRect().width);",
            HINT,
        )
        placed = {"anchored": self._open_hint()}
        self.browser.execute_script("document.activeElement.blur();")
        self.browser.execute_script(NO_ANCHORING)
        placed["not anchored"] = self._open_hint()

        # 18rem under its `?`, slid inside the window; with no anchor positioning,
        # the title's own width under the title
        under = {"gap_is_8px": True, "in_the_window": True}
        assert placed == {
            "anchored": under
            | {"position": "fixed", "width": 288, "spans_its_title": False},
            "not anchored": under
            | {"position": "absolute", "width": title, "spans_its_title": True},
        }

    def test_the_hint_reads_muted_under_a_help_cursor(self):
        self.open_at(reverse("plans:tab_expenses"), 1500)

        look = self.browser.execute_script(
            FIND_TIP + " const s = getComputedStyle(tip); return [s.color, s.cursor];",
            HINT,
        )

        assert look == [INK_MUTED, "help"]

    def _open_hint(self):
        self.browser.execute_script(
            FIND_TIP + " tip.scrollIntoView({block: 'center'});"
            " tip.focus({preventScroll: true});",
            HINT,
        )
        return self.browser.execute_script(HINT_PLACED, HINT)
