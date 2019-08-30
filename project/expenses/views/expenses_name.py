from ...core.mixins.views import CreateAjaxMixin, UpdateAjaxMixin
from .. import forms, models


class New(CreateAjaxMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm


class Update(UpdateAjaxMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
