from ...lib.translation import month_abbr


def test_month_abbr_is_capitalised():
    assert [month_abbr(number) for number in range(1, 13)] == [
        "Sau",
        "Vas",
        "Kov",
        "Bal",
        "Geg",
        "Bir",
        "Lie",
        "Rugp",
        "Rugs",
        "Spa",
        "Lap",
        "Grd",
    ]
