from django.core.exceptions import FieldError
from django.db.models import Count, F, Sum
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ...core.lib import search
from ...core.lib.utils import add_fast_urls, get_action_buttons_html
from ..lib.paginator import CountlessPaginator


class SearchMixin:
    # Set to True in child class to enable fast URLs reverse for update and delete
    # for search results (like expenses list)
    use_fast_urls = False

    def get_context_data(self, **kwargs):
        return (
            super().get_context_data(**kwargs)
            | self.search()
            | get_action_buttons_html()
        )

    def get_search_method(self):
        return getattr(search, self.search_method)

    def search_statistic(self, sql):
        """
        Calculate total price, total quantity and average of search result.

        :param sql: QuerySet
        :return:
            a dictionary with sum_price, sum_quantity and average
            if search_method is 'search_expenses'
        :rtype: dict or None
        """

        if self.search_method not in ["search_expenses"]:
            return {}

        try:
            q = (
                sql.annotate(count=Count("id"))
                .values("count")
                .annotate(
                    sum_price=Sum("price"),
                    sum_quantity=Sum("quantity"),
                )
                .order_by("count")
                .values(
                    "count",
                    "sum_price",
                    "sum_quantity",
                    average=F("sum_price") / F("sum_quantity"),
                )
            )
        except (AttributeError, FieldError):
            return {}

        return q[0] if q else {}

    def search(self):
        search_str = self.request.GET.get("search")

        sql = self.get_search_method()(self.request.user, search_str)
        stats = self.search_statistic(sql)

        page = self.request.GET.get("page", 1)
        paginator = CountlessPaginator(
            query=sql,
            total_records=stats.get("count") or sql.count(),
            per_page=self.per_page,
        )
        page_range = paginator.get_elided_page_range(page)
        page_obj = paginator.get_page(page)

        app = self.request.resolver_match.app_name

        # Add fast URLs if enabled and if the view supports it (like expenses list)
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