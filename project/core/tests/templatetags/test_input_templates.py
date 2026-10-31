import re

import pytest
from django import forms
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


class PageForm(forms.Form):
    text = forms.CharField()
    select = forms.ChoiceField(choices=[("a", "A")])
    checkbox = forms.BooleanField()
    file = forms.FileField()
    sum_price = forms.FloatField()


def _render(source: str, **context) -> str:
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render(context)


@pytest.mark.parametrize(
    "component", ["text", "select", "checkbox", "file", "sum_price"]
)
def test_an_input_given_no_field_draws_none_from_the_page(component):
    # a form view's page context holds a bound `field` of its own
    content = _render(f"<c-input-{component} />", field=PageForm()[component])

    assert not re.search(rf'<(input|select)[^>]*name="{component}"', content)


def test_a_file_input_reads_no_file_chosen_until_one_is():
    content = _render('<c-input-file :field="field" />', field=PageForm()["file"])

    assert (
        '<span class="file-input__name" data-empty="Failas nepasirinktas" '
        'x-text="name || $el.dataset.empty">Failas nepasirinktas</span>'
    ) in content
