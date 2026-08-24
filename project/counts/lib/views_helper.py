from django.urls import reverse_lazy


class CountUrlMixin:
    def get_success_url(self):
        slug = self.object.count_type.slug
        return reverse_lazy("counts:tab_data", kwargs={"slug": slug})
