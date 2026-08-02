from dataclasses import dataclass

from ...services.profile_chart import ProfileLayer, profile_chart_dict


@dataclass(frozen=True)
class _Chart:
    categories: list[str]
    heavy_threshold: float
    text: dict[str, str]
    layers: list[ProfileLayer]


# -------------------------------------------------------------------------------------
#                                                                          ProfileLayer
# -------------------------------------------------------------------------------------
def test_an_empty_layer_has_no_data():
    # the absent layer is this, not a None: a span with no records is a layer
    # the chart simply does not draw
    actual = ProfileLayer()

    assert not actual.has_data
    assert actual.drinking_day_share == []
    assert actual.intensity == []
    assert actual.label == ""


def test_a_layer_of_zeroes_still_has_data():
    # a month drunk on none of its days is a reading, not a missing layer
    actual = ProfileLayer(drinking_day_share=[0.0], intensity=[0.0])

    assert actual.has_data


# -------------------------------------------------------------------------------------
#                                                                    profile_chart_dict
# -------------------------------------------------------------------------------------
def test_chart_dict_carries_the_axis_and_the_layers():
    layer = ProfileLayer(drinking_day_share=[10.0], intensity=[2.0], label="1999")
    chart = _Chart(
        categories=["Jan"], heavy_threshold=6.0, text={"title": "x"}, layers=[layer]
    )

    actual = profile_chart_dict(chart)

    assert actual == {
        "categories": ["Jan"],
        "heavy_threshold": 6.0,
        "text": {"title": "x"},
        "layers": [
            {
                "drinking_day_share": [10.0],
                "intensity": [2.0],
                "label": "1999",
            }
        ],
    }
