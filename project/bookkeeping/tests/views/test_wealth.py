import pytest
from django.urls import reverse

from ....incomes.tests.factories import IncomeFactory

pytestmark = pytest.mark.django_db


def test_content(client_logged):
    IncomeFactory(price=100_000)

    url = reverse("bookkeeping:wealth")
    response = client_logged.get(url)
    content = response.content.decode("utf-8")

    assert "Pinigai" in content
    assert "Turtas" in content
    assert "1.000,00" in content
