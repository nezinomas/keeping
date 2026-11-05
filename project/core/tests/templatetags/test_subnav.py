import re

from django.template.loader import render_to_string

from ...tabs import Tab


def test_the_subnav_scrolls_its_open_tab_into_view():
    tabs = [(Tab("index", "Apžvalga"), "/t/index/"), (Tab("data", "Duomenys"), "/t/")]
    content = render_to_string("cotton/subnav.html", {"tabs": tabs, "active": "data"})

    row = re.search(r'<div class="tabs" role="tablist"[^>]*>', content).group()
    assert (
        "x-init=\"const open = $el.querySelector('[aria-selected=true]');"
        " $el.scrollLeft = open.offsetLeft - $el.offsetLeft"
        ' - ($el.clientWidth - open.offsetWidth) / 2"'
    ) in row
