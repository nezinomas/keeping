from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.views.generic import CreateView, ListView, UpdateView


def update_context(self, context, action):
        plural = self.model._meta.verbose_name_plural

        if action is 'update':
            context['action'] = 'update'
            context['url'] = (
                reverse(
                    f'{plural}:{plural}_update',
                    kwargs={'pk': self.object.pk}
                )
            )

        if action is 'create':
            context['action'] = 'insert'
            context['url'] = reverse(f'{plural}:{plural}_new')


class GetQueryset():
    context_object_name = 'items'

    def get_queryset(self):
        try:
            qs = self.model.objects.year(self.request.user.profile.year)
        except Exception as e1:
            try:
                qs = self.model.objects.items()
            except Exception as e2:
                qs = self.model.objects.all()

        return qs


class GetFormKwargs():
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['year'] = self.request.user.profile.year

        return kwargs


class ListMixin(GetQueryset, GetFormKwargs, LoginRequiredMixin, ListView):
    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_to_string(request)

        return super().dispatch(request, *args, **kwargs)

    def _render_to_string(self, request):
        return (
            render_to_string(
                self.template_name,
                {self.context_object_name: self.get_queryset()},
                request
            )
        )


class CreateMixin(GetQueryset, GetFormKwargs, LoginRequiredMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'create')

        return context


class UpdateMixin(GetQueryset, GetFormKwargs, LoginRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_context(self, context, 'update')

        return context
