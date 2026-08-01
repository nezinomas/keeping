// A recurring-shape profile: one category axis, and the two independent
// questions the Habits tab asks of it — how often a Drink was recorded, and how
// much on the days it was. Drawn for the weekday profile and for the typical
// year, which differ in what a category is and in how many spans they layer.
//
// Layers arrive back to front. The weekday profile sends one; the typical year
// sends the pooled range behind the year the header selects, so the year is
// what a reader sees first and the pooled shape is what they read it against.
function chartDrinksProfile(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // each axis wears its own series' colour, so a reader never has to work out
    // which scale the columns are on and which one the line is on. Declared
    // once here rather than twice, because an axis in one colour and its series
    // in another is worse than neither being coloured at all
    //
    // the front columns are the books chart's: a pale tint of --secondary drawn
    // inside a solid line of it. The rate is a backdrop the intensity line is
    // read against, and a solid block of colour competes with the line for
    // attention. A layer behind it is paler still and has no solid border, so
    // the two never read as one series in two shades
    const rateColor = "var(--secondary)";
    const rateFill = "var(--chart-alpha-25)";
    const backRateFill = "var(--chart-alpha-10)";
    const backRateBorder = "var(--chart-alpha-30)";
    const intensityColor = "var(--chart-color-6)";

    const layers = chartData.layers;
    const series = [];

    layers.forEach(function (layer, index) {
        // the last layer is the reading the chart is about
        const front = index === layers.length - 1;

        // the metric names the series, the layer's own span says which reading
        // of it this is. A single layer needs no span: the tab already names
        // the one year it reads
        const name = (metric) => layer.label ? `${metric} · ${layer.label}` : metric;

        // one layer keeps the width it has always had. Two are stacked in the
        // same slot rather than side by side (see `grouping` below), so the one
        // behind runs the full width and the one in front is narrowed to sit
        // inside it
        let pointPadding = 0.1;
        if (layers.length > 1) {
            pointPadding = front ? 0.18 : 0;
        }

        series.push({
            type: "column",
            name: name(chartData.text.share),
            data: layer.drinking_day_share,
            yAxis: 0,
            color: front ? rateFill : backRateFill,
            borderColor: front ? rateColor : backRateBorder,
            pointPadding: pointPadding,
            zIndex: 1,
            // the legend reads front layer first, whatever order they draw in
            legendIndex: layers.length - 1 - index,
            tooltip: {
                valueSuffix: ` ${chartData.text.share_unit}`
            },
        });

        series.push({
            // the two series answer different questions — how often, and how
            // much when — so each carries its own axis and its own unit in the
            // tooltip, and neither is readable off the other's scale
            type: "line",
            name: name(chartData.text.intensity),
            data: layer.intensity,
            yAxis: 1,
            color: intensityColor,
            // same hue, because it is the same metric: only the weight says
            // which span it belongs to. A dashed, marker-less line reads as the
            // reference shape it is, and never as a second measurement
            lineWidth: front ? 2 : 1.5,
            dashStyle: front ? "Solid" : "ShortDash",
            opacity: front ? 1 : 0.55,
            // above every column, or a backdrop's columns would bury it
            zIndex: 3,
            marker: {
                enabled: front,
                radius: 4,
                symbol: "circle",
            },
            legendIndex: layers.length + (layers.length - 1 - index),
            tooltip: {
                valueSuffix: ` ${chartData.text.intensity_unit}`
            },
        });
    });

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
        },
        title: {
            text: chartData.text.title
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            crosshair: true,
        },
        yAxis: [
            {
                // a share of the times that one category has come round, so it
                // has a ceiling: letting the axis auto-scale past 100 would
                // make a Saturday drunk on every week look like there is room
                // above it
                title: {
                    text: chartData.text.share_unit,
                    style: { color: rateColor },
                },
                labels: {
                    style: { color: rateColor },
                },
                min: 0,
                max: 100,
            },
            {
                // Std Av, deliberately not the drink-type dropdown's unit: the
                // plot line below is defined in Std Av, and a converted series
                // would leave it marking a level the columns no longer measure
                title: {
                    text: chartData.text.intensity_unit,
                    style: { color: intensityColor },
                },
                labels: {
                    style: { color: intensityColor },
                },
                min: 0,
                opposite: true,
                gridLineWidth: 0,
                plotLines: [
                    {
                        color: "#333",
                        width: 2,
                        value: chartData.heavy_threshold,
                        zIndex: 5,
                        label: {
                            text: `${chartData.text.threshold_label}: > ${chartData.heavy_threshold.toFixed(0)} Std Av`,
                            align: "right",
                            x: -5,
                            style: {
                                color: "#333",
                                fontWeight: "bold"
                            }
                        }
                    }
                ]
            }
        ],
        tooltip: {
            shared: true,
        },
        plotOptions: {
            column: {
                borderWidth: 0.5,
                borderRadius: 0,
                groupPadding: 0.1,
                // the two spans are the same twelve months, not twelve pairs of
                // months: side by side they would read as a comparison of
                // neighbours, so they share one slot and differ in width
                grouping: false,
            }
        },
        series: series
    });
};
