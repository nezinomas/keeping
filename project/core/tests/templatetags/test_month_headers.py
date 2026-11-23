import re

from ..utils import render_cotton

ABBREVIATIONS = [
    "Saus.", "Vas.", "Kov.", "Bal.", "Geg.", "Birž.",
    "Liep.", "Rugp.", "Rugs.", "Spal.", "Lapkr.", "Gruod.",
]  # fmt: skip


def test_each_th_holds_the_month_abbreviation():
    assert (
        re.findall(r"<th>(.*?)</th>", render_cotton("<c-month-headers />"))
        == ABBREVIATIONS
    )
