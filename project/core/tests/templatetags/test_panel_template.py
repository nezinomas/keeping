import pytest

from ..utils import render_cotton


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
            '<h2 class="panel__title">Būtinos <span class="panel__hint hint tip bottom" '
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
        # a Switch after the title: the slot carries it, the Panel its state
        pytest.param(
            '<c-panel x-data="{ open:false }" title="Balansas">'
            '<c-slot name="title_control"><span class="panel__control">'
            '<c-switch model="open">Rodyti</c-switch></span></c-slot>slot</c-panel>',
            '<section class="panel" x-data="{ open:false }">\n'
            '    <h2 class="panel__title">Balansas<span class="panel__control">\n'
            '<button type="button" role="switch"',
            id="title-control",
        ),
    ],
)
def test_a_panel_draws_what_it_is_given(source, markup):
    assert markup in render_cotton(source)


def test_the_slot_renders_after_the_title():
    content = render_cotton('<c-panel title="Suvartota"><p>Body</p></c-panel>')

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
    content = render_cotton(
        "<c-panel>slot</c-panel>",
        title="Puslapio",
        subtitle="Puslapio",
        hint="Puslapio",
        table="Puslapio",
        title_control="Tituliniai",
    )

    assert markup not in content
