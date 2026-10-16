import pytest
from django.core.paginator import EmptyPage, PageNotAnInteger
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.paginator import CountlessPage, CountlessPaginator


def test_page_str():
    page = CountlessPage([], 0, 2, 5)
    assert str(page) == "<Page 2>"


@pytest.mark.parametrize(
    "total_pages, current_page, expected",
    [(3, 1, True), (3, 3, True), (1, 1, False)],
    ids=["first_of_three", "last_of_three", "only_page"],
)
def test_page_has_other_pages(total_pages, current_page, expected):
    page = CountlessPage([1, 2, 3], total_pages, current_page, 1)

    assert page.has_other_pages() is expected


@pytest.mark.parametrize(
    ("neighbour", "current_page", "expected"),
    [
        (CountlessPage.next_page_number, 1, 2),
        (CountlessPage.previous_page_number, 2, 1),
    ],
    ids=["next", "previous"],
)
def test_neighbour_page_number(neighbour, current_page, expected):
    page = CountlessPage([1, 2, 3], 3, current_page, 1)

    assert neighbour(page) == expected


@pytest.mark.parametrize(
    ("neighbour", "current_page"),
    [(CountlessPage.next_page_number, 3), (CountlessPage.previous_page_number, 1)],
    ids=["no_next", "no_previous"],
)
def test_neighbour_page_number_past_the_edge(neighbour, current_page):
    with pytest.raises(EmptyPage):
        neighbour(CountlessPage([1, 2, 3], 1, current_page, 3))


def test_page_with_rows_keeps_its_place():
    page = CountlessPage([1, 2], 3, 2, 2).with_rows(["a", "b"])

    assert list(page) == ["a", "b"]
    assert (page.has_previous(), page.has_next(), page.start_index()) == (True, True, 3)


@pytest.mark.parametrize("number", [1.1, "a"])
def test_validate_number_not_integer(number):
    with pytest.raises(PageNotAnInteger):
        CountlessPaginator([], 0, 10).validate_number(number)


def test_validate_number_empty_page():
    with pytest.raises(EmptyPage):
        CountlessPaginator([], 0, 10).validate_number(0)


@pytest.mark.parametrize("number", [1, 2])
def test_validate_number_valid(number):
    assert CountlessPaginator([], 0, 10).validate_number(number) == number


@pytest.mark.parametrize(
    "page_number, expected",
    [
        (1.2, 1),
        ("a", 1),
        (2, 2),
        (2.0, 2),
        ("2.0", 1),
    ],
    ids=["fraction", "letter", "int", "whole_float", "float_string"],
)
def test_get_page(page_number, expected):
    paginator = CountlessPaginator([1, 2, 3], 3, 1)
    page = paginator.get_page(page_number)

    assert page.current_page == expected


ELLIPSIS = CountlessPaginator.ELLIPSIS


@pytest.mark.parametrize(
    "total_records, page, expected",
    [
        (5, 1, [1, 2, 3]),
        (22, 8, [1, 2, ELLIPSIS, 5, 6, 7, 8, 9, 10, 11]),
        (22, 4, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 10, 11]),
        (22, 2, [1, 2, 3, 4, 5, ELLIPSIS, 10, 11]),
        (22, 5, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
    ],
    ids=["few_pages", "middle", "near_start", "start", "no_ellipsis"],
)
def test_elided_page_range(total_records, page, expected):
    paginator = CountlessPaginator(list(range(total_records)), total_records, 2)

    assert list(paginator.get_elided_page_range(page)) == expected


@given(
    total_records=st.integers(0, 500),
    per_page=st.integers(1, 20),
    page=st.integers(1, 10**30),
)
@example(total_records=22, per_page=2, page=999)
def test_elided_page_range_lists_only_pages_that_exist(total_records, per_page, page):
    paginator = CountlessPaginator([], total_records, per_page)

    pages = [i for i in paginator.get_elided_page_range(page) if i != ELLIPSIS]

    assert all(1 <= i <= paginator.total_pages for i in pages)


@pytest.mark.parametrize(
    "object_list, total_records, per_page, expected",
    [
        ([1, 2, 3, 4], 4, 4, 1),
        ([1, 2, 3, 4, 5], 5, 4, 2),
    ],
)
def test_total_pages(object_list, total_records, per_page, expected):
    paginator = CountlessPaginator(object_list, total_records, per_page)

    assert paginator.total_pages == expected
