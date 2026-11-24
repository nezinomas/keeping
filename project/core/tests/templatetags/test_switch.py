from ..utils import render_cotton, switch_attributes, switches


def test_a_switch_presses_and_reads_its_callers_variable():
    # a page's own `model` is not the caller's
    content = render_cotton('<c-switch model="open">Skolos</c-switch>', model="page")

    assert switches(content) == [(switch_attributes("open"), "Skolos")]
