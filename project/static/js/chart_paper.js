// The paper skin's chart half, loaded only by pages wearing `.paper-skin`.
// Colours are `--skin-*` tokens; `var()` resolves in Highcharts' inline SVG styles.
//
// A rule's label: on the right, as the left corner holds the pane name; on a
// paper chip, so a mark crossing the rule never covers it.
function paperRuleLabel(text, color) {
    return {
        useHTML: true,
        align: "right",
        x: -6,
        y: -13,
        text: `<span style="background: var(--skin-paper); padding: 0 4px;`
            + ` color: ${color}; font-family: var(--skin-mono); font-size: 10px;`
            + ` letter-spacing: 0.1em; white-space: nowrap;">${text}</span>`,
    };
}

// The two chart heights. Standard is the theme's; a chart with two panes asks for large.
// `var`, because a re-run page script would throw on a redeclared `const`.
var PAPER_CHART_HEIGHT = { standard: 350, large: 420 };

// The first and last category sit a fixed distance in from the plot edge, so a
// chart of 21 years and one of 12 months keep the same margins at any width.
var PAPER_EDGE_PX = 18;

function paperFixEdges() {
    const axis = this.xAxis[0];
    const last = axis.categories.length - 1;
    if (last < 1) {
        return;
    }

    // a column series widens the range by half a category on each side itself
    const pad = PAPER_EDGE_PX * last / (axis.len - 2 * PAPER_EDGE_PX);
    const offset = axis.minPointOffset || 0;
    const min = offset - pad;
    const max = last + pad - offset;
    if (Math.abs(axis.min - min) > 1e-6 || Math.abs(axis.max - max) > 1e-6) {
        axis.setExtremes(min, max, true, false);
    }
}

// A y-axis title laid flat above the plot, where a rotated one would not fit.
// Its chart merges in `PAPER_PANE_TITLE_SPACE`: room for the name or a rule label.
var PAPER_PANE_TITLE = {
    align: "high",
    rotation: 0,
    offset: 0,
    reserveSpace: false,
    textAlign: "left",
    x: 0,
    y: -18,
    style: { whiteSpace: "nowrap", textOverflow: "clip" },
};
var PAPER_PANE_TITLE_SPACE = { spacingTop: 0, marginTop: 27 };

// The parts of a two-pane chart: a reading on top, bars below. Pieces, not one
// config, because `Highcharts.merge` replaces arrays instead of merging them.
function paperTwoPanes() {
    const blue = "var(--skin-data)";
    const paneTitle = PAPER_PANE_TITLE;

    return {
        base: {
            chart: Highcharts.merge(PAPER_PANE_TITLE_SPACE, {
                height: PAPER_CHART_HEIGHT.large,
                events: { render: paperFixEdges },
            }),
            legend: { enabled: false },
            tooltip: { shared: true },
        },
        xAxis: (categories) => ({
            categories: categories,
            type: "category",
            tickmarkPlacement: "on",
            // the widened edges leave room for a tick past the last category
            labels: { formatter() { return categories[this.pos] ?? ""; } },
        }),
        paneTop: {
            min: 0,
            top: "0%",
            height: "68%",
            title: paneTitle,
        },
        paneBottom: {
            min: 0,
            endOnTick: false,
            // headroom, so the tallest bar's label stays clear of the pane name
            maxPadding: 0.3,
            top: "80%",
            height: "20%",
            offset: 0,
            labels: { style: { color: blue } },
            title: Highcharts.merge(paneTitle, { style: { color: blue } }),
        },
        readingDataLabelStyle: {
            fontFamily: "var(--skin-mono)",
            fontSize: "10px",
            color: "var(--skin-ink)",
            fontWeight: "400",
            textOutline: "none",
        },
        bottomBars: {
            type: "column",
            yAxis: 1,
            color: blue,
            grouping: false,
            maxPointWidth: 28,
            showInLegend: false,
            dataLabels: {
                enabled: true,
                crop: false,
                overflow: "allow",
                style: {
                    fontFamily: "var(--skin-mono)",
                    fontSize: "10px",
                    color: "var(--skin-ink-muted)",
                    textOutline: "none",
                    fontWeight: "400",
                },
                formatter: function () {
                    return this.y > 0 ? Highcharts.numberFormat(this.y, 1) : "";
                },
            },
        },
    };
}

// `colors` is the ordinal ramp Year Comparison draws from — years are ordered,
// so they take steps of one hue, palest year first, rather than a hue each.
Highcharts.setOptions({
    colors: [
        "var(--skin-year-0)",
        "var(--skin-year-1)",
        "var(--skin-year-2)",
        "var(--skin-year-3)",
        "var(--skin-year-4)",
        "var(--skin-year-5)",
    ],
    chart: {
        backgroundColor: "transparent",
        height: PAPER_CHART_HEIGHT.standard,
        spacing: [12, 6, 10, 6],
        style: {
            fontFamily: "var(--skin-body)",
        },
    },
    // the Panel title is drawn in HTML, above the chart (core/CONTEXT.md); a
    // chart with no title of its own would otherwise get Highcharts' default
    title: {
        text: null,
    },
    // recessive axes: one ink baseline, hairline grid, mono labels
    xAxis: {
        lineColor: "var(--skin-ink)",
        lineWidth: 1,
        tickColor: "var(--skin-hair)",
        gridLineWidth: 0,
        // an x label names a month, a weekday or a year, so it reads as a word;
        // the axis title below is chrome and keeps the mono caps
        labels: {
            style: {
                color: "var(--skin-ink-muted)",
                fontFamily: "var(--skin-body)",
                fontSize: "11px",
            },
        },
    },
    yAxis: {
        gridLineColor: "var(--skin-hair-soft)",
        gridLineWidth: 1,
        lineWidth: 0,
        title: {
            style: {
                color: "var(--skin-ink-muted)",
                fontFamily: "var(--skin-mono)",
                fontSize: "10px",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
            },
        },
        labels: {
            style: {
                color: "var(--skin-ink-muted)",
                fontFamily: "var(--skin-mono)",
                fontSize: "10px",
            },
        },
    },
    // The tooltip keeps Highcharts' own colours — no background and no border
    // colour is set here, so the border is drawn in the hovered series' colour.
    // Only the width is: the shared theme switches the border off outright
    // (`borderWidth: 0`), which is why a Drinks tooltip had no edge at all.
    tooltip: {
        borderWidth: 1,
        borderRadius: 3,
        shadow: false,
    },
    // under the plot, set once for every paper chart; each chart still sets `enabled`
    legend: {
        layout: "horizontal",
        align: "center",
        verticalAlign: "bottom",
        floating: false,
        backgroundColor: "transparent",
        itemStyle: {
            color: "var(--skin-ink-muted)",
            fontFamily: "var(--skin-body)",
            fontSize: "12px",
            fontWeight: "400",
        },
        itemHoverStyle: {
            color: "var(--skin-ink)",
        },
    },
    plotOptions: {
        series: {
            // a 2px mark reads as drawn rather than printed heavy
            lineWidth: 2,
            states: {
                hover: {
                    lineWidthPlus: 0,
                    halo: false,
                },
                inactive: {
                    opacity: 0.35,
                },
            },
            dataLabels: {
                color: "var(--skin-ink)",
                style: {
                    fontFamily: "var(--skin-mono)",
                    fontSize: "10px",
                    fontWeight: "400",
                    textOutline: "none",
                },
            },
        },
        column: {
            borderWidth: 0,
            // a surface-coloured gap keeps neighbouring bars from reading as one
            // block of colour
            borderColor: "var(--skin-paper)",
            // Highcharts rounds column corners by default from v11; every other
            // chart in the project turns that off one by one, so the theme does
            // it once for every chart that wears the paper skin
            borderRadius: 0,
        },
    },
});
