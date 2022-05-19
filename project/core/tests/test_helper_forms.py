from types import SimpleNamespace

from ..helpers.helper_forms import set_field_properties


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

    set_field_properties(obj, helper)

    assert obj.fields['x'].widget.attrs['class'] == 'form-control-sm'
    assert not helper.form_show_labels
