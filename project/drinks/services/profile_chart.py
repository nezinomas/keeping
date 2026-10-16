from dataclasses import asdict, dataclass, field

from django.utils.translation import gettext as _


@dataclass(frozen=True)
class ProfileLayer:
    """One span on a profile chart. Empty is a layer with no series, not a None;
    a series ends at the last category reached, not at a 0.0 December."""

    drinking_day_share: list[float] = field(default_factory=list)
    intensity: list[float] = field(default_factory=list)
    label: str = ""

    @classmethod
    def from_points(cls, points, label: str = "") -> "ProfileLayer":
        return cls(
            drinking_day_share=[round(p.drinking_day_share * 100, 1) for p in points],
            intensity=[round(p.intensity, 1) for p in points],
            label=label,
        )

    @property
    def has_data(self) -> bool:
        return bool(self.drinking_day_share)


def profile_chart_dict(chart) -> dict:
    """Composed by hand, not `asdict`: a view model carries values the chart never
    plots."""
    return {
        "categories": chart.categories,
        "heavy_threshold": chart.heavy_threshold,
        "text": chart.text,
        "layers": [asdict(layer) for layer in chart.layers],
    }


def profile_chart_text() -> dict[str, str]:
    return {
        "share": _("Drinking-day rate"),
        "share_unit": "%",
        "intensity": _("Per drinking day"),
        # not display_unit: the Heavy day plot line is defined in Std Av, and a
        # converted series leaves it marking nothing
        "intensity_unit": "Std Av",
        "threshold_label": _("Heavy day"),
    }
