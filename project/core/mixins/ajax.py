from django.http import JsonResponse
from django.template.loader import render_to_string

from .get import GetQueryset
from .helpers import format_url_name


class AjaxCreateUpdateMixin():
    list_template_name = None
    object = None

    def get_template_names(self):
        if self.template_name is None:
            plural = format_url_name(self.model._meta.verbose_name)
            app_name = self.request.resolver_match.app_name
            return [f'{app_name}/includes/{plural}_form.html']
        else:
            return [self.template_name]

    def get(self, request, *args, **kwargs):
        if 'pk' in self.kwargs:
            self.object = self.get_object()

        if request.is_ajax():
            data = dict()
            context = self.get_context_data()
            self._render_form(data, context)

            return JsonResponse(data)
        else:
            return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = super(GetQueryset, self).get_queryset()

        return context

    def form_valid(self, form):
        data = dict()
        context = self.get_context_data()

        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
            data['html_list'] = (
                render_to_string(
                    self._get_list_template_name(), context, self.request)
            )
        else:
            data['form_is_valid'] = False

        self._render_form(data, context)

        if self.request.is_ajax():
            return JsonResponse(data)
        else:
            return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        context = self.get_context_data()
        data = dict()

        if self.request.is_ajax():
            self._render_form(data, context)
            return JsonResponse(data)
        else:
            return response

    def _render_form(self, data, context):
        data['html_form'] = (
            render_to_string(self.get_template_names(), context, request=self.request)
        )

        form = self.get_form()
        js_url = []

        for js in form.media._js:  # for all the scripts used by the form
            js_url.append(form.media.absolute_path(js))

        data['js'] = js_url

    def _get_list_template_name(self):
        app_name = self.request.resolver_match.app_name
        plural = format_url_name(self.model._meta.verbose_name)

        if not self.list_template_name:
            return f'{app_name}/includes/{plural}_list.html'
        else:
            return self.list_template_name
