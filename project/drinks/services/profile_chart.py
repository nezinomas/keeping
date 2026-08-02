from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ProfileLayer:
    """One span of time on a Habits profile chart: its two series, and its name.

    The profile charts ask two independent questions of a span — how often a
    Drink was recorded, and how much on the days it was — so a layer carries
    both and nothing else. `label` names the span in the legend, and is empty
    when the tab already names it: the Weekday profile reads the one year the
    header selects, the Typical year draws two spans at once and must say which
    is which.

    Empty is a state rather than a null. A span with no records is a layer with
    no series, and a chart draws only the layers that have data — so nothing
    downstream has to ask whether a layer is there before reading it.

    Inside a series a null does appear, and means one thing only: a category the
    span never reached, which the chart draws as a gap. A running year's
    December plotted as 0.0 would read as a month without a Drink instead.
    """

    drinking_day_share: list[float | None] = field(default_factory=list)
    intensity: list[float | None] = field(default_factory=list)
    label: str = ""

    @property
    def has_data(self) -> bool:
        return bool(self.drinking_day_share)


def profile_chart_dict(chart) -> dict:
    """The JSON a profile chart needs: one category axis and its layers.

    Layers arrive back to front, so the last one is the reading the chart is
    about — the one that gets the solid fill and the markers. Composed by hand
    rather than by `asdict`, because a view model may also carry values the
    chart never plots.
    """
    return {
        "categories": chart.categories,
        "heavy_threshold": chart.heavy_threshold,
        "text": chart.text,
        "layers": [asdict(layer) for layer in chart.layers],
    }
