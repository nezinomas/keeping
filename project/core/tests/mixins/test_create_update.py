import re

import pytest
from django import forms
from django.template.loader import render_to_string
from django.views.generic.base import ContextMixin

from ...lib.form_widgets import DatePickerWidget, YearPickerWidget
from ...mixins.create_update import CreateUpdateMixin
from ...mixins.delete import DeleteMixin
from ..utils import PICKER_SCRIPT


@pytest.mark.parametrize(
    "mixin, template, submits",
    [
        pytest.param(
            CreateUpdateMixin, "core/generic_form.html", 0, id="create_update"
        ),
        pytest.param(DeleteMixin, "core/generic_delete_form.html", 1, id="delete"),
    ],
)
def test_a_bare_view_renders_an_empty_modal(mixin, template, submits):
    class BareView(mixin, ContextMixin):
        pass

    actual = render_to_string(template, BareView().get_context_data())

    assert re.search(r'<form[^>]*hx-post=""', actual)
    assert '<h5 class="modal-title"></h5>' in actual
    # no form_action, no insert or update button
    assert actual.count('type="submit"') == submits
    assert not re.findall(PICKER_SCRIPT, actual)


@pytest.mark.parametrize(
    "name, field, scripts",
    [
        pytest.param(
            "day",
            forms.DateField(widget=DatePickerWidget()),
            ["date-picker.js"],
            id="date_widget",
        ),
        pytest.param(
            "season",
            forms.IntegerField(widget=YearPickerWidget()),
            ["year-picker.js"],
            id="year_widget",
        ),
        pytest.param("date", forms.DateField(), [], id="date_name"),
        pytest.param("year", forms.IntegerField(), [], id="year_name"),
    ],
)
def test_a_form_loads_the_picker_of_its_widget_not_its_field_name(name, field, scripts):
    form = forms.Form()
    form.fields[name] = field

    actual = render_to_string("core/generic_form.html", {"form": form})

    assert re.findall(PICKER_SCRIPT, actual) == scripts
