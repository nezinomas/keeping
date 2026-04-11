from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


class CssClassMixin:
    modal_body_css_class = "plans-form"


class PlanQuerySetMixin:
    def get_tall_queryset(self):
        qs = self.service_class(self.request.user).items()

        # Filter using exactly the kwargs provided in the URL
        # If the URL is incomes/1999/5/, self.kwargs is {'year': 1999, 'income_type_id': 5}        # noqa: E501
        # qs.filter(**self.kwargs) translates instantly to qs.filter(year=1999, income_type_id=5)  # noqa: E501
        return qs.filter(**self.kwargs)


class PlanUpdateMixin(PlanQuerySetMixin):
    def get_object(self, queryset=None):
        if obj := self.get_tall_queryset().first():
            return obj

        raise Http404(_("No plans found."))

    def url(self):
        if not self.object:
            return None

        return reverse_lazy(f"plans:{self.url_name}", kwargs=self.kwargs)


class PlanDeleteMixin(PlanQuerySetMixin):
    def get_object(self, queryset=None):
        if obj := self.get_tall_queryset().first():
            return obj

        raise Http404(_("No plans found."))

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.get_tall_queryset().delete()
        return response

    def url(self):
        if not self.object:
            return None

        return reverse_lazy(f"plans:{self.url_name}", kwargs=self.kwargs)
