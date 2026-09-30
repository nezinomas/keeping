import re

from django.template import engines
from django_cotton.compiler_regex import CottonCompiler

FULL = [
    "Sausis", "Vasaris", "Kovas", "Balandis", "Gegužė", "Birželis",
    "Liepa", "Rugpjūtis", "Rugsėjis", "Spalis", "Lapkritis", "Gruodis",
]  # fmt: skip

SHORT = [
    "sau", "vas", "kov", "bal", "geg", "bir",
    "lie", "rugp", "rugs", "spa", "lap", "grd",
]  # fmt: skip


def _render():
    processed = CottonCompiler().process("<c-month-headers />")
    return engines["django"].from_string(processed).render({})


def test_renders_twelve_th_cells():
    assert len(re.findall(r"<th>", _render())) == 12


def test_each_th_holds_the_full_name_in_month_full():
    actual = re.findall(
        r'<span class="month-table__month-full">(.*?)</span>', _render()
    )

    assert actual == FULL


def test_each_th_holds_a_short_name_in_month_short():
    actual = re.findall(
        r'<span class="month-table__month-short">(.*?)</span>', _render()
    )

    assert actual == SHORT
