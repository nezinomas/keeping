// The paper skin, chart half: what every Drinks chart shares once the page is
// wearing `.drinks-skin`.
//
// The shared Highcharts theme belongs to every other app too, so none of this
// can go there. It is scoped the same way `chart_drinks_legend.js` is — by
// loading: `drinks/index.html` is the only page that pulls this file in, and the
// only page that draws these charts. Loaded after the legend file, so the legend
// keeps the position set there and only gains its type from here.
//
// The colours are the `--skin-*` tokens the wrapper defines, read straight out
// of the cascade: Highcharts writes them into inline SVG styles inside the
// wrapper, so `var()` resolves. One place defines the palette, in SCSS.
//
// A label for a rule across the plot — a Limit, a guideline, a threshold.
//
// It is drawn as HTML on a paper chip rather than as SVG text, because a bar or a
// line that crosses the rule would otherwise be drawn over the label naming it:
// the rule a mark is measured against has to stay readable exactly where marks
// reach it.
function drinksRuleLabel(text, color, align) {
    const toRight = align === "right";

    return {
        useHTML: true,
        align: toRight ? "right" : "left",
        x: toRight ? -6 : 6,
        y: -13,
        text: `<span style="background: var(--skin-paper); padding: 0 4px;`
            + ` color: ${color}; font-family: var(--skin-mono); font-size: 10px;`
            + ` letter-spacing: 0.1em; white-space: nowrap;">${text}</span>`,
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
        spacing: [12, 6, 10, 6],
        style: {
            fontFamily: "var(--skin-body)",
        },
    },
    title: {
        align: "left",
        margin: 24,
        style: {
            color: "var(--skin-ink)",
            fontFamily: "var(--skin-mono)",
            fontSize: "11px",
            fontWeight: "400",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
        },
    },
    subtitle: {
        align: "left",
        style: {
            color: "var(--skin-ink-muted)",
            fontFamily: "var(--skin-mono)",
            fontSize: "10px",
            letterSpacing: "0.1em",
        },
    },
    // recessive axes: one ink baseline, hairline grid, mono labels
    xAxis: {
        lineColor: "var(--skin-ink)",
        lineWidth: 1,
        tickColor: "var(--skin-hair)",
        gridLineWidth: 0,
        labels: {
            style: {
                color: "var(--skin-ink-muted)",
                fontFamily: "var(--skin-mono)",
                fontSize: "10px",
                letterSpacing: "0.08em",
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
    legend: {
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
        },
    },
});
