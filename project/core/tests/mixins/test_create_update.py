import pytest
from django.template.loader import render_to_string
from django.views.generic.base import ContextMixin

from ...mixins.create_update import CreateUpdateMixin
from ...mixins.delete import DeleteMixin


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

    assert 'hx-post=""' in actual
    assert '<h5 class="modal-title"></h5>' in actual
    # no form_action, no insert or update button
    assert actual.count('type="submit"') == submits
