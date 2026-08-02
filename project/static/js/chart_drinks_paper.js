// The paper skin, chart half: what every Drinks chart shares once the page is
// wearing `.drinks-skin`.
//
// The shared Highcharts theme belongs to every other app too, so none of this
// can go there. It is scoped the same way `chart_drinks_legend.js` is — by
// loading: `drinks/index.html` is the only page that pulls this file in, and the
// only page that draws these charts. Loaded after the legend file, so the legend
// keeps the position set there and only gains its type from here.
//
// The colours are the `--drinks-*` tokens the wrapper defines, read straight out
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
        text: `<span style="background: var(--drinks-paper); padding: 0 4px;`
            + ` color: ${color}; font-family: var(--drinks-mono); font-size: 10px;`
            + ` letter-spacing: 0.1em; white-space: nowrap;">${text}</span>`,
    };
}

// `colors` is the ordinal ramp Year Comparison draws from — years are ordered,
// so they take steps of one hue, palest year first, rather than a hue each.
Highcharts.setOptions({
    colors: [
        "var(--drinks-year-0)",
        "var(--drinks-year-1)",
        "var(--drinks-year-2)",
        "var(--drinks-year-3)",
        "var(--drinks-year-4)",
        "var(--drinks-year-5)",
    ],
    chart: {
        backgroundColor: "transparent",
        spacing: [12, 6, 10, 6],
        style: {
            fontFamily: "var(--drinks-body)",
        },
    },
    title: {
        align: "left",
        margin: 24,
        style: {
            color: "var(--drinks-ink)",
            fontFamily: "var(--drinks-mono)",
            fontSize: "11px",
            fontWeight: "400",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
        },
    },
    subtitle: {
        align: "left",
        style: {
            color: "var(--drinks-ink-muted)",
            fontFamily: "var(--drinks-mono)",
            fontSize: "10px",
            letterSpacing: "0.1em",
        },
    },
    // recessive axes: one ink baseline, hairline grid, mono labels
    xAxis: {
        lineColor: "var(--drinks-ink)",
        lineWidth: 1,
        tickColor: "var(--drinks-hair)",
        gridLineWidth: 0,
        labels: {
            style: {
                color: "var(--drinks-ink-muted)",
                fontFamily: "var(--drinks-mono)",
                fontSize: "10px",
                letterSpacing: "0.08em",
            },
        },
    },
    yAxis: {
        gridLineColor: "var(--drinks-hair-soft)",
        gridLineWidth: 1,
        lineWidth: 0,
        title: {
            style: {
                color: "var(--drinks-ink-muted)",
                fontFamily: "var(--drinks-mono)",
                fontSize: "10px",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
            },
        },
        labels: {
            style: {
                color: "var(--drinks-ink-muted)",
                fontFamily: "var(--drinks-mono)",
                fontSize: "10px",
            },
        },
    },
    tooltip: {
        // the two literals on this page. Highcharts parses these two through its
        // own colour code rather than handing them to the DOM, and a `var()` it
        // cannot parse comes out black — so they are written out, and they track
        // $drinks-paper and $drinks-ink in abstracts/_variables.scss
        backgroundColor: "#ffffff",
        borderColor: "#16222b",
        borderRadius: 0,
        borderWidth: 1,
        shadow: false,
        style: {
            color: "var(--drinks-ink)",
            fontFamily: "var(--drinks-body)",
            fontSize: "12px",
        },
    },
    legend: {
        backgroundColor: "transparent",
        itemStyle: {
            color: "var(--drinks-ink-muted)",
            fontFamily: "var(--drinks-body)",
            fontSize: "12px",
            fontWeight: "400",
        },
        itemHoverStyle: {
            color: "var(--drinks-ink)",
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
                color: "var(--drinks-ink)",
                style: {
                    fontFamily: "var(--drinks-mono)",
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
            borderColor: "var(--drinks-paper)",
        },
    },
});
