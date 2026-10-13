from collections.abc import Callable

from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ...users.models import User
from ..lib.paginator import CountlessPaginator
from ..lib.utils import add_fast_urls, get_action_buttons_html


def count_only(qs):
    return {"count": qs.count()}


class SearchMixin:
    search_method: Callable[[User, str], QuerySet]
    per_page: int
    search_totals = staticmethod(count_only)
    use_fast_urls = False

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
        page_obj = paginator.get_page(self.request.GET.get("page", 1))
        page_range = paginator.get_elided_page_range(page_obj.current_page)

        app = self.request.resolver_match.app_name

        if self.use_fast_urls:
            page_obj.object_list = add_fast_urls(list(page_obj.object_list), app)

        return {
            "notice": _("No data found"),
            "object_list": page_obj,
            "search": search_str,
            "url": reverse(f"{app}:search"),
            "paginator_object": {
                "total_pages": paginator.total_pages,
                "page_range": page_range,
                "ELLIPSIS": paginator.ELLIPSIS,
            },
            **stats,
        }
