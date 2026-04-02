class AddUserToKwargsMixin:
    def get_form_kwargs(self, **kwargs):
        kwargs["user"] = self.request.user
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