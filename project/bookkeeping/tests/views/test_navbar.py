import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _active_links(client, path: str) -> list[str]:
    content = client.get(path).content.decode()

    return re.findall(r'<div class="active">\s*<a href="([^"]+)"', content)


@pytest.mark.parametrize(
    "path",
    ["/detailed/", "/detailed/incomes/", "/detailed/savings/", "/detailed/expenses/"],
)
def test_the_navbar_marks_detailed_on_every_tab(client_logged, path):
    assert _active_links(client_logged, path) == [reverse("bookkeeping:detailed")]


def test_the_navbar_still_marks_expenses_on_expenses(client_logged):
    assert _active_links(client_logged, "/expenses/") == [reverse("expenses:index")]
