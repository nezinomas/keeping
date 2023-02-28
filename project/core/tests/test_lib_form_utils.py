from types import SimpleNamespace

from ..lib.form_utils import add_css_class


# ----------------------------------------------------------------------------
#                                                         set_field_properties
# ----------------------------------------------------------------------------
def test_set_field_properties():
    obj = SimpleNamespace(
        fields={
            'x': SimpleNamespace(
                widget=SimpleNamespace(attrs={'class': None})
            )
        })

    helper = SimpleNamespace(form_show_labels=True)

    add_css_class(obj, helper)

    assert obj.fields['x'].widget.attrs['class'] == 'form-control-sm'
    assert not helper.form_show_labels
