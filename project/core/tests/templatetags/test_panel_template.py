import pytest
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def _render(source: str, **context) -> str:
    # <c-…> tags are only rewritten by the cotton loader when a template is
    # loaded by name; run the same compiler by hand to render one from a string.
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render(context)


@pytest.mark.parametrize(
    "source, markup",
    [
        pytest.param(
            '<c-panel title="Suvartota per mėnesį">slot</c-panel>',
            '<h2 class="panel__title">Suvartota per mėnesį</h2>',
            id="title",
        ),
        pytest.param(
            '<c-panel title="Suvartota" subtitle="Antraštė">slot</c-panel>',
            '<p class="panel__subtitle">Antraštė</p>',
            id="subtitle",
        ),
        pytest.param(
            '<c-panel title="Suvartota" id="chart-x-container">slot</c-panel>',
            '<section class="panel" id="chart-x-container">',
            id="id",
        ),
        pytest.param(
            '<c-panel table title="Suvartota">slot</c-panel>',
            '<section class="panel panel--table"',
            id="table",
        ),
        pytest.param(
            '<c-panel title="Būtinos" hint="Kodėl būtinos">slot</c-panel>',
            '<h2 class="panel__title">Būtinos <span class="panel__hint hint tip right" '
            'tabindex="0" data-tip="Kodėl būtinos" aria-label="Kodėl būtinos">'
            '<i class="bi bi-question-circle"></i></span></h2>',
            id="hint",
        ),
        pytest.param(
            '<c-panel table title="Suvartota" subtitle="Antraštė" id="breakdown">'
            "slot</c-panel>",
            '<section class="panel panel--table" id="breakdown">\n'
            '    <h2 class="panel__title">Suvartota</h2>\n'
            '    <p class="panel__subtitle">Antraštė</p>',
            id="table-keeps-the-rest",
        ),
        # a title that is a control: the slot carries its text, the Panel its state
        pytest.param(
            '<c-panel x-data="{ open:false }"><c-slot name="title_control">'
            '<a role="button">Prognozė</a></c-slot>slot</c-panel>',
            '<section class="panel" x-data="{ open:false }">\n'
            '    <h2 class="panel__title"><a role="button">Prognozė</a></h2>',
            id="title-control",
        ),
    ],
)
def test_a_panel_draws_what_it_is_given(source, markup):
    assert markup in _render(source)


def test_the_slot_renders_after_the_title():
    content = _render('<c-panel title="Suvartota"><p>Body</p></c-panel>')

    assert content.index("panel__title") < content.index("<p>Body</p>")


@pytest.mark.parametrize(
    "markup",
    [
        pytest.param('<h2 class="panel__title">Puslapio', id="title"),
        pytest.param("panel__subtitle", id="subtitle"),
        pytest.param("panel__hint", id="hint"),
        pytest.param("panel--table", id="table"),
        # a page's own `title_control` is not the slot
        pytest.param('<h2 class="panel__title">Tituliniai', id="title-control"),
    ],
)
def test_a_panel_draws_nothing_it_is_not_given(markup):
    content = _render(
        "<c-panel>slot</c-panel>",
        title="Puslapio",
        subtitle="Puslapio",
        hint="Puslapio",
        table="Puslapio",
        title_control="Tituliniai",
    )

    assert markup not in content
