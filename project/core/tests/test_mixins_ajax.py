from types import SimpleNamespace

import mock
import pytest

from ..factories import UserFactory
from ..mixins.ajax import AjaxCreateUpdateMixin
from .utils import setup_view


@pytest.fixture()
def _request(rf):
    request = rf.get('/fake/')
    request.user = UserFactory.build()
    request.resolver_match = SimpleNamespace(app_name='app_name')

    return request


@mock.patch('project.incomes.models.Income')
def test_template_names_set_automatically(mck, _request):
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxCreateUpdateMixin):
        template_name = None
        model = mck

    v = setup_view(Dummy(), _request)

    actual = v.get_template_names()
    expect = 'app_name/includes/plurals_form.html'

    assert actual[0] == expect


@mock.patch('project.incomes.models.Income')
def test_template_names(mck, _request):
    mck._meta.verbose_name = 'plural'

    class Dummy(AjaxCreateUpdateMixin):
        template_name = 'XXX'
        model = mck

    v = setup_view(Dummy(), _request)

    actual = v.get_template_names()
    expect = 'XXX'

    assert actual[0] == expect
