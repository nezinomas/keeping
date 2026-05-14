from django.utils.translation import gettext_lazy as _

from ...lib.form_widgets import DatePickerWidget, YearPickerWidget


def test_date_picker_widget_default_attrs():
    widget = DatePickerWidget()
    assert widget.attrs["class"] == "date-picker"
    assert widget.attrs["placeholder"] == str(_("Select a date"))
    assert widget.format == "%Y-%m-%d"


def test_date_picker_widget_with_custom_attrs():
    custom = {"data-test": "123", "class": "custom-class"}
    widget = DatePickerWidget(attrs=custom)
    expected = {
        "class": "custom-class",  # ← overrides default
        "placeholder": str(_("Select a date")),
        "data-test": "123",
    }
    assert widget.attrs == expected


def test_date_picker_widget_merge_preserves_default():
    widget = DatePickerWidget(attrs={"id": "date-input"})
    assert widget.attrs["class"] == "date-picker"
    assert "id" in widget.attrs


def test_year_picker_widget_default_attrs():
    widget = YearPickerWidget()
    assert widget.attrs["class"] == "year-picker"
    assert widget.attrs["placeholder"] == str(_("Select a year"))


def test_year_picker_widget_with_custom_attrs():
    custom = {"data-year": "2025", "class": "my-year"}
    widget = YearPickerWidget(attrs=custom)
    expected = {
        "class": "my-year",
        "placeholder": str(_("Select a year")),
        "data-year": "2025",
    }
    assert widget.attrs == expected


def test_year_picker_widget_no_override_without_attrs():
    widget = YearPickerWidget()
    assert "class" in widget.attrs
    assert "placeholder" in widget.attrs


def test_date_picker_empty_attrs():
    widget = DatePickerWidget(attrs={})
    assert widget.attrs["class"] == "date-picker"


def test_year_picker_none_attrs():
    widget = YearPickerWidget(attrs=None)
    assert widget.attrs["class"] == "year-picker"
    assert widget.attrs["placeholder"] == str(_("Select a year"))


def test_date_picker_uses_gettext_lazy(mocker):
    mocker.patch("project.core.lib.form_widgets._", return_value="Translated Date")

    widget = DatePickerWidget()
    assert widget.attrs["placeholder"] == "Translated Date"
