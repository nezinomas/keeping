import re

from django.template import engines
from django_cotton.compiler_regex import CottonCompiler

SWITCH = re.compile(
    r"<button\b([^>]*)>\s*"
    r'<span class="switch__track" aria-hidden="true">'
    r'<span class="switch__knob"></span></span>\s*'
    r'<span class="switch__label">([^<]*)</span>\s*</button>'
)
ATTRIBUTE = re.compile(r'([:@\w-]+)="([^"]*)"')


def _render(source: str, **context) -> str:
    # <c-…> tags are only rewritten by the cotton loader when a template is
    # loaded by name; run the same compiler by hand to render one from a string.
    processed = CottonCompiler().process(source)
    return engines["django"].from_string(processed).render(context)


def test_a_switch_presses_and_reads_its_callers_variable():
    # a page's own `model` is not the caller's
    content = _render('<c-switch model="open">Skolos</c-switch>', model="page")

    assert [
        (dict(ATTRIBUTE.findall(attrs)), label)
        for attrs, label in SWITCH.findall(content)
    ] == [
        (
            {
                "type": "button",
                "role": "switch",
                "class": "switch",
                ":aria-checked": "open ? 'true' : 'false'",
                "@click": "open = ! open",
            },
            "Skolos",
        )
    ]
