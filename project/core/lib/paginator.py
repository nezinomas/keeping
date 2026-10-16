import collections
import contextlib
from collections.abc import Iterator

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


class CountlessPage(collections.abc.Sequence):
    def __init__(
        self,
        object_list: QuerySet | list,
        total_pages: int,
        current_page: int,
        page_size: int,
    ):
        self.object_list = object_list
        self.total_pages = total_pages
        self.current_page = current_page
        self.page_size = page_size

        self._has_next = self.current_page < total_pages
        self._has_previous = self.current_page > 1

    def __repr__(self):
        return f"<Page {self.current_page}>"

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        return self.object_list[index]

    def with_rows(self, rows: list) -> "CountlessPage":
        return CountlessPage(rows, self.total_pages, self.current_page, self.page_size)

    def has_next(self):
        return self._has_next

    def has_previous(self):
        return self._has_previous

    def has_other_pages(self):
        return self.has_next() or self.has_previous()

    def next_page_number(self):
        if self.has_next():
            return self.current_page + 1
        raise EmptyPage(_("Next page does not exist"))

    def previous_page_number(self):
        if self.has_previous():
            return self.current_page - 1
        raise EmptyPage(_("Previous page does not exist"))

    def start_index(self):
        return (self.current_page - 1) * self.page_size + 1


class CountlessPaginator:
    ELLIPSIS = "…"

    def __init__(self, query: QuerySet | list, total_records: int, per_page: int):
        self.query = query
        self.total_records = total_records
        self.per_page = per_page

    def validate_number(self, raw_number) -> int:
        try:
            if isinstance(raw_number, float) and not raw_number.is_integer():
                raise ValueError
            number = int(raw_number)
        except (TypeError, ValueError) as e:
            raise PageNotAnInteger(_("Page number is not an integer")) from e

        if number < 1:
            raise EmptyPage(_("Page number is less than 1"))

        return number

    def get_page(self, raw_page) -> CountlessPage:
        number = 1
        with contextlib.suppress(PageNotAnInteger, EmptyPage):
            number = self.validate_number(raw_page)
        return self.page(number)

    def page(self, current_page: int) -> CountlessPage:
        # a page past the end is empty without a query: its offset can overflow the DB
        query = []
        if current_page <= self.total_pages:
            bottom = (current_page - 1) * self.per_page
            query = self.query[bottom : bottom + self.per_page]

        return CountlessPage(query, self.total_pages, current_page, self.per_page)

    def paging(self, raw_page) -> tuple[CountlessPage, dict]:
        page = self.get_page(raw_page)
        paginator_object = {
            "total_pages": self.total_pages,
            "page_range": self.get_elided_page_range(page.current_page),
            "ELLIPSIS": self.ELLIPSIS,
        }
        return page, paginator_object

    @property
    def page_range(self) -> range:
        return range(1, self.total_pages + 1)

    @property
    def total_pages(self) -> int:
        return (self.total_records + self.per_page - 1) // self.per_page

    def get_elided_page_range(
        self, number=1, *, on_each_side=3, on_ends=2
    ) -> Iterator[int | str]:
        """Django's elided range: page 43 of 50 → 1, 2, …, 40–46, …, 49, 50."""
        page = min(self.validate_number(number), self.total_pages)

        if self.total_pages <= (on_each_side + on_ends) * 2:
            yield from self.page_range
            return

        if page > (1 + on_each_side + on_ends) + 1:
            yield from range(1, on_ends + 1)
            yield self.ELLIPSIS
            yield from range(page - on_each_side, page + 1)
        else:
            yield from range(1, page + 1)

        if page < (self.total_pages - on_each_side - on_ends) - 1:
            yield from range(page + 1, page + on_each_side + 1)
            yield self.ELLIPSIS
            yield from range(self.total_pages - on_ends + 1, self.total_pages + 1)
        else:
            yield from range(page + 1, self.total_pages + 1)
