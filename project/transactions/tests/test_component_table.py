import pytest
from django.http import HttpResponse
from django.template import Context, Template, loader


@pytest.fixture(name="table")
def fixture_table(fake_request):
    def _func(ctx):
        template = loader.get_template("cotton/transactions_table.html")

        return (
            HttpResponse(template.render(ctx, fake_request))
            .content.decode("utf-8")
            .replace("\n", "")
            .replace("\t", "")
            .replace("  ", "")
        )

    return _func


def test_no_request_in_context(table):
    ctx = {"request": None, "object_list": []}

    actual = table(ctx)

    assert "<b>xxxx</b> metais įrašų nėra." in actual


def test_request_in_context(table, fake_request):
    ctx = {"request": fake_request, "object_list": []}

    actual = table(ctx)

    assert "<b>1999</b> metais įrašų nėra." in actual
