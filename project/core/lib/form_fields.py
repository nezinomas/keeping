from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelChoiceIterator

from .form_widgets import DecimalCommaWidget


class CommaFloatField(forms.FloatField):
    # a Lithuanian keyboard sends the decimal separator as a comma, verbatim
    widget = DecimalCommaWidget

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace(",", ".")

        return super().to_python(value)


class PreloadedModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        for obj in self.field.preloaded_objects:
            yield self.choice(obj)

    def __len__(self):
        return len(self.field.preloaded_objects) + (self.field.empty_label is not None)

    def __bool__(self):
        return self.field.empty_label is not None or bool(self.field.preloaded_objects)


class PreloadedModelChoiceField(forms.ModelChoiceField):
    # answers from preload(), so a formset sharing one load queries once, not
    # per form; `queryset` stays set because Django requires one

    iterator = PreloadedModelChoiceIterator

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preloaded_objects = ()
        self._by_pk = {}

    def preload(self, objects):
        self.preloaded_objects = tuple(objects)
        self._by_pk = {str(obj.pk): obj for obj in self.preloaded_objects}
        self.widget.choices = self.choices

    def to_python(self, value):
        if value in self.empty_values:
            return super().to_python(value)

        self.validate_no_null_characters(value)
        if str(value) not in self._by_pk:
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        return self._by_pk[str(value)]
