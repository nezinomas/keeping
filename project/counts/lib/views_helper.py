import contextlib

from django.urls import reverse_lazy

from .. import models
from ..services.model_services import CountTypeModelService


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
                self.kwargs["object"] = self.object
