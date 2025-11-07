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
from . import forms, models, services
from .services.model_services import BookModelService, BookTargetModelService


class Index(TemplateViewMixin):
    template_name = "books/index.html"

    def get_context_data(self, **kwargs):
        context = {
            "year": self.request.user.year,
            "tab": self.request.GET.get("tab"),
            "info_row": rendered_content(self.request, InfoRow, **self.kwargs),
            "books": rendered_content(self.request, Lists, **self.kwargs),
        }
        return super().get_context_data(**kwargs) | context


class ChartReaded(TemplateViewMixin):
    template_name = "books/readed_books.html"

    def get_context_data(self, **kwargs):
        data = services.ChartReadedData(self.request.user)
        obj = services.ChartReaded(data)

        # if not data.readed:
        #     self.template_name = "empty.html"
        #     return {}

        return super().get_context_data(**kwargs) | {"chart": obj.context()}


class InfoRow(TemplateViewMixin):
    template_name = "books/info_row.html"

    def get_context_data(self, **kwargs):
        obj = services.InfoRow(self.request.user)
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
        user = self.request.user
        service = BookModelService(user)
        return service.objects if self.request.GET.get("tab") else service.year(user.year)

    def get_context_data(self, **kwargs):
        page = self.request.GET.get("page", 1)
        sql = self.get_queryset()
        paginator = CountlessPaginator(
            query=sql, total_records=len(sql), per_page=self.per_page
        )
        page_range = paginator.get_elided_page_range(page=page)

        context = {
            "object_list": paginator.get_page(page),
            "url": reverse("books:list"),
            "tab": self.request.GET.get("tab"),
            "first_item": paginator.count - (paginator.per_page * (int(page) - 1)),
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
    success_url = reverse_lazy("books:list")
    modal_form_title = _("New book")


class Update(UpdateViewMixin):
    model = models.Book
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("books:list")
    modal_form_title = _("Update book")


class Delete(DeleteViewMixin):
    model = models.Book
    success_url = reverse_lazy("books:list")
    modal_form_title = _("Delete book")


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
    url = reverse_lazy("books:target_new")
    modal_form_title = _("New goal")


class TargetUpdate(UpdateViewMixin):
    model = models.BookTarget
    hx_trigger_django = "afterTarget"
    form_class = forms.BookTargetForm
    modal_form_title = _("Update goal")
