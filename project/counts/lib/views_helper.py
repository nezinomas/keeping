import contextlib
from dataclasses import dataclass, field
from datetime import datetime

from django.db.models import Sum
from django.urls import reverse_lazy

from ...users.models import User
from .. import models
from ..services.model_services import CountModelService, CountTypeModelService


class CountUrlMixin:
    def get_success_url(self):
        slug = self.object.count_type.slug
        return reverse_lazy("counts:tab_data", kwargs={"slug": slug})


class CountTypetObjectMixin:
    object = None

    def get_object(self):
        self.object = self.kwargs.get("object")

        if self.object:
            return

        if count_type_slug := self.kwargs.get("slug"):
            with contextlib.suppress(models.CountType.DoesNotExist):
                self.object = CountTypeModelService(self.request.user).objects.get(
                    slug=count_type_slug
                )

                # push self.object to self.kwargs
                self.kwargs["object"] = self.object


@dataclass
class InfoRowData:
    user: User
    slug: str
    year: int = field(init=False, default=None)
    total: int = field(init=False, default=0)
    gap: int = field(init=False, default=0)

    def __post_init__(self):
        self.year = self.user.year
        self.gap = self._get_gap(self.year, self.slug)
        self.total = self._get_total(self.year, self.slug)

    def _get_total(self, year, slug):
        qs_total = (
            CountModelService(self.user)
            .objects.filter(count_type__slug=slug, date__year=year)
            .aggregate(total=Sum("quantity"))
        )

        return qs_total.get("total") or 0

    def _get_gap(self, year, slug):
        gap = 0

        if year == datetime.now().year:
            with contextlib.suppress(models.Count.DoesNotExist):
                qs_latest = (
                    CountModelService(self.user)
                    .objects.filter(count_type__slug=slug)
                    .latest()
                )
                gap = (datetime.now().date() - qs_latest.date).days

        return gap
