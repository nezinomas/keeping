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
