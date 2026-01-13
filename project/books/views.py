from typing import cast

from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.paginator import CountlessPaginator
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    rendered_content,
)
from ..users.models import User
from . import forms, models, services
from .services.model_services import BookModelService


class Index(TemplateViewMixin):
    template_name = "books/index.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        year = cast(int, user.year)
        context = {
            "year": year,
            "tab": self.request.GET.get("tab"),
            "info_row": rendered_content(self.request, InfoRow, **self.kwargs),
            "books": rendered_content(self.request, Lists, **self.kwargs),
        }
        return super().get_context_data(**kwargs) | context


class ChartReaded(TemplateViewMixin):
    template_name = "books/readed_books.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        data = services.ChartReadedData(user)
        obj = services.ChartReaded(data)

        return super().get_context_data(**kwargs) | {"chart": obj.context()}


class InfoRow(TemplateViewMixin):
    template_name = "books/info_row.html"

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        obj = services.InfoRow(user)
        context = {
            "readed": obj.readed,
            "reading": obj.reading,
            "target": obj.target,
        }
        return super().get_context_data(**kwargs) | context


class Lists(ListViewMixin):
    model = models.Book
    per_page = 50

    def get_queryset(self):
        user = cast(User, self.request.user)
        year = cast(int, user.year)
        service = BookModelService(user)
        return service.objects if self.request.GET.get("tab") else service.year(year)

    def get_context_data(self, **kwargs):
        page = int(self.request.GET.get("page", 1))
        sql = self.get_queryset()
        paginator = CountlessPaginator(
            query=sql, total_records=len(sql), per_page=self.per_page
        )
        page_range = paginator.get_elided_page_range(page=page)

        context = {
            "object_list": paginator.get_page(page),
            "url": reverse("books:list"),
            "tab": self.request.GET.get("tab"),
            "first_item": paginator.count - paginator.per_page * (page - 1),
            "paginator_object": {
                "total_pages": paginator.total_pages,
                "page_range": page_range,
                "ELLIPSIS": paginator.ELLIPSIS,
            },
        }

        return super().get_context_data(**kwargs) | context


class New(CreateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    modal_form_title = _("New book")
    success_url = reverse_lazy("books:list")


class Update(UpdateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    modal_form_title = _("Update book")
    success_url = reverse_lazy("books:list")


class Delete(DeleteViewMixin):
    model = models.Book
    modal_form_title = _("Delete book")
    success_url = reverse_lazy("books:list")


class Search(SearchViewMixin):
    template_name = "books/book_list.html"
    per_page = 50

    search_method = "search_books"


# --------------------------------------------------------------------------------------
#                                                                          Target Views
# --------------------------------------------------------------------------------------
class TargetNew(CreateViewMixin):
    model = models.BookTarget
    hx_trigger_django = "afterTarget"
    form_class = forms.BookTargetForm
    url_name = "target_new"
    modal_form_title = _("New goal")


class TargetUpdate(UpdateViewMixin):
    model = models.BookTarget
    hx_trigger_django = "afterTarget"
    form_class = forms.BookTargetForm
    url_name = "target_update"
    modal_form_title = _("Update goal")
