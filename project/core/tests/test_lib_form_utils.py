from types import SimpleNamespace

from ..lib.form_utils import add_css_class


def test_set_field_properties():
    obj = SimpleNamespace(
        fields={"x": SimpleNamespace(widget=SimpleNamespace(attrs={"class": None}))}
    )

    add_css_class(obj)

    assert obj.fields["x"].widget.attrs["class"] == "form-control-sm"


def test_set_field_properties_have_css():
    obj = SimpleNamespace(
        fields={"x": SimpleNamespace(widget=SimpleNamespace(attrs={"class": "X"}))}
    )

    add_css_class(obj)

    assert obj.fields["x"].widget.attrs["class"] == "form-control-sm X"
