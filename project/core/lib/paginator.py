import collections

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _


class CountlessPage(collections.abc.Sequence):
    def __init__(self, object_list, current_page, page_size):
        self.object_list = object_list
        self.current_page = current_page
        self.page_size = page_size

        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)

        self._has_next = len(self.object_list) > len(self.object_list[: self.page_size])
        self._has_previous = self.current_page > 1

    def __repr__(self):
        return f"<Page {self.current_page}>"

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError
        return self.object_list[index]

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


class CountlessPaginator:
    ELLIPSIS = "…"

    def __init__(self, object_list, per_page) -> None:
        self.object_list = object_list
        self.per_page = per_page

    def validate_number(self, number):
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError) as e:
            raise PageNotAnInteger(_("Page number is not an integer")) from e

        if number < 1:
            raise EmptyPage(_("Page number is less than 1"))

        return number

    def get_page(self, number):
        try:
            number = self.validate_number(number)
        except (PageNotAnInteger, EmptyPage):
            number = 1
        return self.page(number)

    def page(self, current_page):
        current_page = self.validate_number(current_page)
        bottom = (current_page - 1) * self.per_page
        top = bottom + self.per_page
        return CountlessPage(self.object_list[bottom:top], current_page, self.per_page)

    @property
    def page_range(self):
        return range(1, self.num_pages + 1)

    @property
    def num_pages(self):
        return len(self.object_list) // self.per_page + 1

    @property
    def count(self):
        return len(self.object_list)

    def get_elided_page_range(self, number=1, *, on_each_side=3, on_ends=2):
        """
        Return a 1-based range of pages with some values elided.

        If the page range is larger than a given size, the whole range is not
        provided and a compact form is returned instead, e.g. for a paginator
        with 50 pages, if page 43 were the current page, the output, with the
        default arguments, would be:

            1, 2, …, 40, 41, 42, 43, 44, 45, 46, …, 49, 50.
        """
        number = self.validate_number(number)

        if self.num_pages <= (on_each_side + on_ends) * 2:
            yield from self.page_range
            return

        if number > (1 + on_each_side + on_ends) + 1:
            yield from range(1, on_ends + 1)
            yield self.ELLIPSIS
            yield from range(number - on_each_side, number + 1)
        else:
            yield from range(1, number + 1)

        if number < (self.num_pages - on_each_side - on_ends) - 1:
            yield from range(number + 1, number + on_each_side + 1)
            yield self.ELLIPSIS
            yield from range(self.num_pages - on_ends + 1, self.num_pages + 1)
        else:
            yield from range(number + 1, self.num_pages + 1)
