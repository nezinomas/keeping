import re

import pytest
from django.urls import reverse

from ...models import Debt
from .. import factories

pytestmark = pytest.mark.django_db


def test_debts_index_not_logged(client):
    url = reverse("debts:index")
    response = client.get(url)

    assert response.status_code == 302


def test_debts_index_renders_its_four_lists(client_logged):
    factories.BorrowReturnFactory()
    factories.LendReturnFactory()

    url = reverse("debts:index")
    response = client_logged.get(url)
    content = response.content.decode()

    assert "Borrow Remark" in content
    assert "Borrow Return Remark" in content
    assert "Lend Remark" in content
    assert "Lend Return Remark" in content


@pytest.mark.parametrize(
    "url_name, debt_type, label",
    [
        pytest.param("debts:new", "borrow", "Skolą", id="borrow"),
        pytest.param("debts:return_new", "borrow", "Sumą", id="borrow_return"),
        pytest.param("debts:new", "lend", "Skolą", id="lend"),
        pytest.param("debts:return_new", "lend", "Sumą", id="lend_return"),
    ],
)
def test_debts_index_add_button(client_logged, url_name, debt_type, label):
    url = reverse("debts:index")
    response = client_logged.get(url)

    content = response.content.decode()

    link = reverse(url_name, kwargs={"debt_type": debt_type})
    pattern = re.compile(rf'<button.*?hx-get="{link}".*?>(.*?)<\/button>')
    res = re.findall(pattern, content)

    assert res[0] == label


@pytest.mark.parametrize(
    "method, path",
    [
        pytest.param("get", "/debts/x/lists/", id="list"),
        pytest.param("get", "/debts/x/new/", id="new"),
        pytest.param("post", "/debts/x/new/", id="create"),
        pytest.param("get", "/debts/x/return/lists/", id="return_list"),
    ],
)
def test_debts_url_of_an_unknown_type_is_404(client_logged, method, path):
    response = getattr(client_logged, method)(path, {"name": "Name", "price": "1"})

    assert response.status_code == 404
    assert not Debt.objects.exists()
