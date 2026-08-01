// Where every Drinks chart puts its legend: under the plot, centred.
//
// The shared Highcharts theme floats the legend in the top-right corner, which
// is the same row as the title. That holds for a two-entry legend and breaks for
// anything wider — the typical year names two metrics over two spans, and its
// legend covered the title outright. Rather than repeat the override in every
// chart that grew a third series, it is set once here.
//
// Only the position is set. Whether a legend shows at all stays each chart's own
// call: the overview, weekly and heavy-day charts label their single series in
// the axis title and switch it off.
//
// Scoped to Drinks by loading: `drinks/index.html` is the only page that pulls
// this in, and it is also the only page that draws these charts.
Highcharts.setOptions({
    legend: {
        layout: "horizontal",
        align: "center",
        verticalAlign: "bottom",
        floating: false,
    },
});
