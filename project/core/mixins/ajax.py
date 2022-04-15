from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from .get import GetQuerysetMixin


class AjaxCreateUpdateMixin(GetQuerysetMixin):
    #Todo: delete this class
    pass


class AjaxDeleteMixin(GetQuerysetMixin):
    #Todo: delete this class
    pass

class AjaxCustomFormMixin(LoginRequiredMixin, FormView):
    #Todo: delete this class
    pass


class AjaxSearchMixin(AjaxCustomFormMixin):
    # Todo: delete this class
    pass
