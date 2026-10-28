// The paper skin's chart half, loaded only by pages wearing `.paper-skin`.
// Colours are `--skin-*` tokens; `var()` resolves in Highcharts' inline SVG styles.

// A chart's small text: every axis label and title, figure on a mark and rule label.
// `var`, because a re-run page script would throw on a redeclared `const`.
var PAPER_CHART_TEXT_PX = 12;
var PAPER_CHART_TEXT = {
    fontFamily: "var(--skin-display)",
    fontSize: `${PAPER_CHART_TEXT_PX}px`,
};

// A rule's label, on the right, as the left corner holds the pane name; its chip is
// `skin/_chart.scss`'s. `state` is "muted" for a guide, "harm" for a limit.
function paperRuleLabel(text, state = "muted") {
    return {
        useHTML: true,
        align: "right",
        x: -6,
        y: -13, // the chip clears its rule
        text: `<span class="chart-rule-label chart-rule-label--${state}">${text}</span>`,
    };
}

// The two chart heights. Standard is the theme's; a chart with two panes asks for large.
var PAPER_CHART_HEIGHT = { standard: 350, large: 420 };

// Read once, at the table headers' breakpoint: below it a chart's text is cut to fit.
var PAPER_WIDE = window.matchMedia("(min-width: 768px)").matches;

// Every figure printed on a mark; each use adds only its colour.
var PAPER_DATA_LABEL_STYLE = {
    ...PAPER_CHART_TEXT,
    fontWeight: "400",
    textOutline: "none",
};

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

// A y-axis title laid flat above the plot, where a rotated one would not fit. It rises
// this far; its chart's top margin holds the rise and the title's line above it.
var PAPER_PANE_TITLE_RISE = 18;
var PAPER_PANE_TITLE = {
    align: "high",
    rotation: 0,
    offset: 0,
    reserveSpace: false,
    textAlign: "left",
    x: 0,
    y: -PAPER_PANE_TITLE_RISE,
    style: { whiteSpace: "nowrap", textOverflow: "clip" },
};
var PAPER_PANE_TITLE_SPACE = { marginTop: PAPER_PANE_TITLE_RISE + PAPER_CHART_TEXT_PX };

// The parts of a two-pane chart: a reading on top, bars below. Pieces, not one
// config, because `Highcharts.merge` replaces arrays instead of merging them.
function paperTwoPanes() {
    const blue = "var(--skin-data)";
    // the bottom pane takes what the top pane and the gap between them leave
    const topHeight = 68;
    const gap = 12;

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
            height: `${topHeight}%`,
            title: PAPER_PANE_TITLE,
        },
        paneBottom: {
            min: 0,
            endOnTick: false,
            // headroom, so the tallest bar's label stays clear of the pane name
            maxPadding: 0.3,
            top: `${topHeight + gap}%`,
            height: `${100 - topHeight - gap}%`,
            offset: 0,
            labels: { style: { color: blue } },
            title: Highcharts.merge(PAPER_PANE_TITLE, { style: { color: blue } }),
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
                // the theme's `dataLabels.color` beats a `style.color`
                color: "var(--skin-ink-muted)",
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
            fontFamily: PAPER_CHART_TEXT.fontFamily,
        },
    },
    // the Panel title is drawn in HTML, above the chart (core/CONTEXT.md); a
    // chart with no title of its own would otherwise get Highcharts' default
    title: {
        text: null,
    },
    xAxis: {
        lineColor: "var(--skin-ink)",
        lineWidth: 1,
        tickColor: "var(--skin-hair)",
        gridLineWidth: 0,
        labels: {
            style: {
                color: "var(--skin-ink-muted)",
                ...PAPER_CHART_TEXT,
            },
        },
    },
    yAxis: {
        gridLineColor: "var(--skin-hair-soft)",
        gridLineWidth: 1,
        lineWidth: 0,
        // written as in a sentence, over the caps `themes/theme.js` gives a legacy chart
        title: {
            style: {
                color: "var(--skin-ink-muted)",
                ...PAPER_CHART_TEXT,
                textTransform: "none",
            },
        },
        labels: {
            style: {
                color: "var(--skin-ink-muted)",
                ...PAPER_CHART_TEXT,
            },
        },
    },
    // Highcharts' own colours, so the border takes the hovered series' colour; only
    // its width is set, as `themes/theme.js` turns the border off (`borderWidth: 0`).
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
            ...PAPER_CHART_TEXT,
            fontSize: "13px",
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
                style: PAPER_DATA_LABEL_STYLE,
            },
        },
        column: {
            borderWidth: 0,
            // a surface-coloured gap keeps neighbouring bars from reading as one
            // block of colour
            borderColor: "var(--skin-paper)",
            // Highcharts rounds column corners from v11; the paper skin's are square
            borderRadius: 0,
        },
    },
});
