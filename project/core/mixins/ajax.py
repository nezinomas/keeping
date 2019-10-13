from django.http import JsonResponse
from django.template.loader import render_to_string

from .get import GetFormKwargsMixin, GetQuerysetMixin
from .helpers import format_url_name, template_name


class AjaxCreateUpdateMixin(GetQuerysetMixin, GetFormKwargsMixin):
    list_template_name = None
    object = None

    def get_template_names(self):
        if self.template_name is None:
            return [template_name(self, 'form')]
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        data = dict()

        if form.is_valid():
            form.save()

            context = self.get_context_data()
            context['form'] = form

            data['form_is_valid'] = True
            data['html_list'] = (
                render_to_string(
                    self._get_list_template_name(), context, self.request)
            )

        self._render_form(data, context)

        if self.request.is_ajax():
            return JsonResponse(data)
        else:
            return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data()

        context['form'] = form
        data = {'form_is_valid': False}

        if self.request.is_ajax():
            self._render_form(data, context)
            return JsonResponse(data)
        else:
            return super().form_invalid(form)

    def _render_form(self, data, context):
        data['html_form'] = (
            render_to_string(self.get_template_names(),
                             context, request=self.request)
        )

        #  comment code which extracts js files from form.media._js
        #  and append to data['js'] dictionary
        #  then ajax.js loads these files with jquery function $.getScript()
        #  ToDo: delete after some time
        #  code commented on 2019.09.17

        # form = self.get_form()
        # js_url = []

        # for js in form.media._js:  # for all the scripts used by the form
        #     js_url.append(form.media.absolute_path(js))

        # data['js'] = js_url

    def _get_list_template_name(self):
        if not self.list_template_name:
            return template_name(self, 'list')
        else:
            return self.list_template_name
