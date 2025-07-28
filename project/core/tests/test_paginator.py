import pytest
from django.core.paginator import EmptyPage, PageNotAnInteger

from ..lib.paginator import CountlessPage, CountlessPaginator


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


@pytest.mark.parametrize(
    "number",
    [(1.1), ("a")],
)
@pytest.mark.xfail(raises=PageNotAnInteger)
def test_validate_number_not_integer(number):
    CountlessPaginator([], 10).validate_number(number)


@pytest.mark.xfail(raises=EmptyPage)
def test_validate_number_empty_page():
    CountlessPaginator([], 10).validate_number(0)


def test_validate_number_valid():
    paginator = CountlessPaginator([], 10)

    assert paginator.validate_number(1) == 1
    assert paginator.validate_number(2) == 2


@pytest.mark.parametrize(
    "page_number, expected",
    [
        (1.2, 1),
        ("a", 1),
        (2, 2),
        (2.0, 2),
        ("2.0", 1),
    ],
)
def test_get_page(page_number, expected):
    paginator = CountlessPaginator([1, 2, 3], 1)
    page = paginator.get_page(page_number)

    assert page.number == expected


def test_elided_page_range_1():
    paginator = CountlessPaginator(list(range(1, 5)), 2)
    page_range = paginator.get_elided_page_range()

    assert list(page_range) == [1, 2, 3]


def test_elided_page_range_2():
    paginator = CountlessPaginator(list(range(1, 22)), 2)
    page_range = paginator.get_elided_page_range(8)

    assert list(page_range) == [
        1,
        2,
        CountlessPaginator.ELLIPSIS,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
    ]


def test_elided_page_range_3():
    paginator = CountlessPaginator(list(range(1, 22)), 2)
    page_range = paginator.get_elided_page_range(4)

    assert list(page_range) == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        CountlessPaginator.ELLIPSIS,
        10,
        11,
    ]


def test_elided_page_range_4():
    paginator = CountlessPaginator(list(range(1, 22)), 2)
    page_range = paginator.get_elided_page_range(2)

    assert list(page_range) == [1, 2, 3, 4, 5, CountlessPaginator.ELLIPSIS, 10, 11]


def test_elided_page_range_5():
    paginator = CountlessPaginator(list(range(1, 22)), 2)
    page_range = paginator.get_elided_page_range(5)

    assert list(page_range) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
