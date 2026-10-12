from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


class PlanFormMixin:
    template_name = "plans/plan_form.html"


class PlanQuerySetMixin:
    def get_tall_queryset(self):
        qs = self.service_class(self.request.user).items()

        # the URL's kwargs are the filter: incomes/1999/5/ -> year, income_type_id
        return qs.filter(**self.kwargs)


class PlanObjectMixin(PlanQuerySetMixin):
    def get_object(self, queryset=None):
        if obj := self.get_tall_queryset().first():
            return obj

        raise Http404(_("No plans found."))

    def url(self):
        return reverse_lazy(f"plans:{self.url_name}", kwargs=self.kwargs)


class PlanDeleteMixin(PlanObjectMixin):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.get_tall_queryset().delete()
        return response
