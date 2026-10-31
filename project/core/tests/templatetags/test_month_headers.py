import re

from django.template import engines
from django_cotton.compiler_regex import CottonCompiler

ABBREVIATIONS = [
    "Saus.", "Vas.", "Kov.", "Bal.", "Geg.", "Birž.",
    "Liep.", "Rugp.", "Rugs.", "Spal.", "Lapkr.", "Gruod.",
]  # fmt: skip


def _render():
    processed = CottonCompiler().process("<c-month-headers />")
    return engines["django"].from_string(processed).render({})


def test_each_th_holds_the_month_abbreviation():
    assert re.findall(r"<th>(.*?)</th>", _render()) == ABBREVIATIONS
