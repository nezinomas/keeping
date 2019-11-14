from ..lib import utils


class FormMixin():
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = utils.get_user()
        if commit:
            instance.save()
        return instance
