import pytest
from django.template import Context, Template

from ..templatetags.table import table


@pytest.fixture
def _template():
    template = Template(
        '{% load table %}'
        '{% table "transactions:transactions_update" %}'
    )
    return template


def test_no_request_in_context(_template):
    ctx = Context({'request': None, 'items': []})

    actual = _template.render(ctx)

    assert '<b>XXXX</b> metais įrašų nėra.' in actual
