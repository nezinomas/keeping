import pytest

from ...core.tests.utils import setup_view
from ...users.factories import UserFactory
from ..views import BookTabMixin


# ---------------------------------------------------------------------------------------
#                                                                            BookTabMixin
# ---------------------------------------------------------------------------------------
@pytest.fixture()
def _rf(rf):
    def _wrapper(url, **kwargs):
        request = rf.get(url, **kwargs)
        request.user = UserFactory.build()
        return request
    return _wrapper


@pytest.fixture(params=[
    {'url': '/f/?tab=xxx', 'expect': 'index'},
    {'url': '/f/?tab=index', 'expect': 'index'},
    {'url': '/f/?tab=all', 'expect': 'all'},
    {'url': '/f/', 'expect': 'index'},
    {'url': '', 'expect': 'index'},
])
def _rf_params(request):
    return request.param


def test_book_tab_mixin_request_get(_rf_params, _rf):
    request = _rf(_rf_params['url'])

    class Dummy(BookTabMixin):
        pass

    v = setup_view(Dummy(), request)
    actual = v.get_tab()

    assert actual == _rf_params['expect']


@pytest.mark.parametrize(
    'url, arg, expect', [
        ('/f/', 'index', 'index'),
        ('/f/', 'all', 'all'),
        ('/f/?tab=index', 'all', 'index'),
        ('/f/?tab=all', 'index', 'all'),
    ])
def test_book_tab_mixin_request_tab_in_kwargs(url, arg, expect, _rf):
    request = _rf(url)

    class Dummy(BookTabMixin):
        pass

    v = setup_view(Dummy(), request)
    v.kwargs = {"tab": arg}
    actual = v.get_tab()

    assert actual == expect
