import pytest

from ..lib.paginator import CountlessPage


def test_page_str():
    page = CountlessPage([], 2, 5)
    assert str(page) == "<Page 2>"


def test_page_has_other_pages():
    page = CountlessPage([1, 2, 3], 1, 1)
    assert page.has_other_pages()

    page = CountlessPage([1, 2, 3], 3, 1)
    assert page.has_other_pages()

    page = CountlessPage([1, 2, 3], 1, 3)
    assert not page.has_other_pages()


def test_next_page_number():
    page = CountlessPage([1, 2, 3], 1, 1)
    assert page.next_page_number() == 2


@pytest.mark.xfail()
def test_next_page_number_no_next():
    CountlessPage([1, 2, 3], 3, 3).next_page_number()


def test_prev_page_number():
    page = CountlessPage([1, 2, 3], 2, 1)
    assert page.previous_page_number() == 1


@pytest.mark.xfail()
def test_prev_page_number_no_prev():
    CountlessPage([1, 2, 3], 1, 3).previous_page_number()
