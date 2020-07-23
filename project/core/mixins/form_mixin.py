from ...counters.models import CounterType
from ..lib import utils
from django.core.exceptions import ObjectDoesNotExist

class FormForUserMixin():
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = utils.get_user()

        if commit:
            instance.save()

        return instance


class FormForCounterTypeMixin():
    def save(self, counter_type, commit=True):
        instance = super().save(commit=False)

        try:
            _counter = CounterType.objects.get(title=counter_type)
        except ObjectDoesNotExist:
            return instance

        instance.counter_type = _counter

        if commit:
            instance.save()

        return instance
