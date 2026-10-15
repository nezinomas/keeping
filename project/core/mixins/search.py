from collections.abc import Callable
from typing import TypedDict

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from ...users.models import User
from ..lib.paginator import CountlessPaginator
from ..lib.utils import get_action_buttons_html

PER_PAGE = 50


class SearchTotals(TypedDict):
    count: int


def count_only(qs: QuerySet) -> SearchTotals:
    return {"count": qs.count()}


def keep_rows(rows: list) -> list:
    return rows


class SearchMixin:
    search_method: Callable[[User, str], QuerySet]
    per_page = PER_PAGE
    search_totals = staticmethod(count_only)
    search_rows = staticmethod(keep_rows)

    def get_context_data(self, **kwargs):
        return (
            super().get_context_data(**kwargs)
            | self.search()
            | get_action_buttons_html()
        )

    def search(self):
        search_str = self.request.GET.get("search", "")

        sql = self.search_method(self.request.user, search_str)
        stats = self.search_totals(sql)

        paginator = CountlessPaginator(
            query=sql,
            total_records=stats["count"],
            per_page=self.per_page,
        )
        page_obj, paginator_object = paginator.paging(self.request.GET.get("page", 1))
        rows = self.search_rows(list(page_obj.object_list))

        return {
            "notice": _("No data found"),
            "object_list": page_obj.with_rows(rows),
            "search": search_str,
            "url": self.request.path,
            "paginator_object": paginator_object,
            **stats,
        }
