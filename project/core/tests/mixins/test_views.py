import re

import pytest
from django.urls import reverse

from ....accounts.tests.factories import AccountFactory
from ....savings.tests.factories import SavingTypeFactory

pytestmark = pytest.mark.django_db

OPTION = re.compile(r'<option value="\d+">([^<]*)</option>')


@pytest.mark.parametrize(
    "url_name, factory",
    [
        pytest.param("transactions:load_saving_type", SavingTypeFactory, id="fund"),
        pytest.param("accounts:load", AccountFactory, id="account"),
    ],
)
@pytest.mark.parametrize(
    "data_of, listed",
    [
        pytest.param(
            lambda source: {"from_account": source.pk}, ["Other"], id="source"
        ),
        pytest.param(lambda source: {}, [], id="no-value"),
        pytest.param(lambda source: {"from_account": ""}, [], id="empty"),
        pytest.param(lambda source: {"from_account": "x"}, [], id="not-a-number"),
        pytest.param(lambda source: {"from_account": "0"}, [], id="zero"),
    ],
)
def test_a_load_view_lists_the_journals_open_items_but_the_source(
    client_logged, second_user, url_name, factory, data_of, listed
):
    source = factory(title="Source")
    factory(title="Other")
    factory(title="Closed", closed=1000)
    factory(title="Foreign", journal=second_user.journal)

    actual = client_logged.get(reverse(url_name), data_of(source)).content.decode()

    assert OPTION.findall(actual) == listed
