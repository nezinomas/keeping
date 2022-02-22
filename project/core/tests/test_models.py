import pytest

from ..factories import TitleDummyFactory

pytestmark = pytest.mark.django_db


def test_title_build():
    m = TitleDummyFactory()

    assert m.title == 'Title'
    assert m.slug == 'title'


@pytest.mark.xfail
def test_title_long():
    actual = TitleDummyFactory.build(title='x'*26)

    actual.full_clean()


@pytest.mark.xfail
def test_title_short():
    actual = TitleDummyFactory.build(title='xx')

    actual.full_clean()
