from datetime import date

from django.utils.functional import cached_property


class TodayMixin:
    """The one today every figure and form of a request is computed from."""

    @cached_property
    def today(self) -> date:
        return date.today()


class FormKwargsMixin(TodayMixin):
    def get_form_kwargs(self, **kwargs):
        kwargs["user"] = self.request.user
        kwargs["today"] = self.today
        return kwargs

    def get_form(self, data=None, files=None, **kwargs):
        kwargs = self.get_form_kwargs(**kwargs)
        return self.form_class(data, files, **kwargs)

    def get_formset_class(self):
        # capture methods
        base_form = self.form_class
        get_kwargs = self.get_form_kwargs

        class UserAwareForm(base_form):
            def __init__(self, *args, **form_kwargs):
                form_kwargs = get_kwargs(**form_kwargs)  # using captured closure
                super().__init__(*args, **form_kwargs)

        return UserAwareForm
