from ...core.mixins.views import CreateAjaxMixin, UpdateAjaxMixin
from .. import forms, models


class UpdateContext():
    list_template_name = 'expenses/includes/expenses_type_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = models.ExpenseType.objects.items()
        return context


class New(UpdateContext, CreateAjaxMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm


class Update(UpdateContext, UpdateAjaxMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
