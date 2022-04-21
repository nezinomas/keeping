import pytest
from django.template import Context, Template


@pytest.fixture
def _template():
    template = Template(
        '{% load table %}'
        '{% table "transactions:update" "transactions:delete" %}'
    )
    return template


def test_no_request_in_context(_template):
    ctx = Context({'request': None, 'items': []})

    actual = _template.render(ctx)

    assert '<b>xxxx</b> metais įrašų nėra.' in actual


def test_request_in_context(_template, fake_request):
    ctx = Context({'request': fake_request, 'items': []})

    actual = _template.render(ctx)

    assert '<b>1999</b> metais įrašų nėra.' in actual
