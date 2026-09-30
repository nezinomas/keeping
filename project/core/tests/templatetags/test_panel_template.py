from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def _render(source: str) -> str:
    # <c-…> tags are only rewritten by the cotton loader when a template is
    # loaded by name; run the same compiler by hand to render one from a string.
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render({})


def test_the_title_renders_inside_the_panel_title():
    content = _render('<c-panel title="Suvartota per mėnesį">slot</c-panel>')

    assert '<h2 class="panel__title">Suvartota per mėnesį</h2>' in content


def test_the_slot_renders_after_the_title():
    content = _render('<c-panel title="Suvartota"><p>Body</p></c-panel>')

    assert content.index("panel__title") < content.index("<p>Body</p>")


def test_a_subtitle_renders_when_given():
    content = _render('<c-panel title="Suvartota" subtitle="Antraštė">slot</c-panel>')

    assert '<p class="panel__subtitle">Antraštė</p>' in content


def test_no_subtitle_element_when_none_is_given():
    content = _render('<c-panel title="Suvartota">slot</c-panel>')

    assert "panel__subtitle" not in content


def test_an_id_attribute_lands_on_the_section():
    content = _render(
        '<c-panel title="Suvartota" id="chart-x-container">slot</c-panel>'
    )

    assert '<section class="panel" id="chart-x-container">' in content


def test_a_table_panel_carries_the_modifier_class():
    content = _render('<c-panel table title="Suvartota">slot</c-panel>')

    assert '<section class="panel panel--table"' in content


def test_a_table_panel_keeps_its_title_subtitle_and_id():
    content = _render(
        '<c-panel table title="Suvartota" subtitle="Antraštė" id="breakdown">'
        "slot</c-panel>"
    )

    assert '<section class="panel panel--table" id="breakdown">' in content
    assert '<h2 class="panel__title">Suvartota</h2>' in content
    assert '<p class="panel__subtitle">Antraštė</p>' in content


def test_a_hint_renders_a_question_tip_inside_the_title():
    content = _render('<c-panel title="Būtinos" hint="Kodėl būtinos">slot</c-panel>')

    assert '<h2 class="panel__title">Būtinos <span class="panel__hint tip' in content
    assert 'data-tip="Kodėl būtinos"' in content
    assert 'aria-label="Kodėl būtinos"' in content
    assert '<i class="bi bi-question-circle"></i>' in content


def test_no_hint_element_when_none_is_given():
    content = _render('<c-panel title="Suvartota">slot</c-panel>')

    assert "panel__hint" not in content
