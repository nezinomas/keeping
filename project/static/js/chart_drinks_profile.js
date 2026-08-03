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
    const rateColor = "var(--drinks-data)";
    const rateFill = "var(--drinks-data-tint)";
    const backRateFill = "var(--drinks-data-faint)";
    const backRateBorder = "var(--drinks-data-edge)";
    // the one chart on a Tab that carries two measures rather than two spans of
    // one, so the Intensity takes the skin's second hue. Not harm: harm marks a
    // reading that is harmful, and an Intensity is only read against a threshold
    const intensityColor = "var(--drinks-second)";

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
            // read by the tooltip formatter below, which groups by span and so
            // needs the metric on its own — `name` carries both
            metric: chartData.text.share,
            unit: chartData.text.share_unit,
            layerLabel: layer.label,
            // the axis colour, not the column's: a 10%-alpha backdrop fill is
            // invisible as a tooltip bullet, and the metric is what the bullet
            // is there to identify — the span is already the group's heading
            dotColor: rateColor,
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
            metric: chartData.text.intensity,
            unit: chartData.text.intensity_unit,
            layerLabel: layer.label,
            dotColor: intensityColor,
        });
    });

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
            // each axis picks its own ticks. Aligning them across two axes is
            // there to make one set of gridlines fit both, and the intensity
            // axis draws none — all it does here is override the rate axis'
            // tickInterval to match the intensity's tick count
            alignTicks: false,
        },
        title: {
            text: chartData.text.title
        },
        legend: {
            // position comes from chart_drinks_legend.js — under the plot, where
            // four entries naming two metrics over two spans have room to sit
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
                // has a ceiling — but a rate that lives well under it spends the
                // rest of the plot on empty air, and the shape the tab is about
                // flattens. So the axis ends at the rate this reader actually
                // reaches, rounded up to the next ten, rather than at a level
                // picked for anyone: how often a Drink is recorded differs by an
                // order of magnitude between accounts, and any fixed cap is
                // wasted air for one of them and a wall for another
                title: {
                    text: chartData.text.share_unit,
                    style: { color: rateColor },
                },
                labels: {
                    style: { color: rateColor },
                },
                // zero is where a rate starts, so it is the one end that stays
                // fixed: a share read off a floating baseline is not a share
                min: 0,
                // and the top never runs past the ceiling the metric itself has
                ceiling: 100,
                // tens, so the labels stay round however far up the axis goes
                tickInterval: 10,
                // no headroom above the tallest column: the padding is what
                // would push a 29% peak onto the tick after the one it needs
                maxPadding: 0,
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
                        // ink, not harm: nothing on this chart turns red for
                        // crossing it, so the rule is a level rather than a
                        // verdict — and harm beside the Intensity's own hue
                        // would read as a third series
                        color: "var(--drinks-ink-muted)",
                        width: 1.5,
                        dashStyle: "Dash",
                        value: chartData.heavy_threshold,
                        zIndex: 5,
                        label: drinksRuleLabel(
                            `${chartData.text.threshold_label}: > ${chartData.heavy_threshold.toFixed(0)} Std Av`,
                            "var(--drinks-ink-muted)"
                        )
                    }
                ]
            }
        ],
        tooltip: {
            shared: true,
            // the rate columns are a pale tint, so the border would be near
            // invisible if it took the hovered series' own colour
            borderColor: rateColor,
            // one block per span, not four flat rows. The column and the line
            // of a span are two readings of that span and belong together —
            // side by side with another span's pair, a reader has to match four
            // rows back to their series names to see which is which
            formatter: function () {
                if (!this.points || !this.points.length) {
                    return false;
                }

                const groups = [];
                this.points.forEach(function (point) {
                    const label = point.series.userOptions.layerLabel;
                    let group = groups.find((candidate) => candidate.label === label);
                    if (!group) {
                        group = { label: label, points: [] };
                        groups.push(group);
                    }
                    group.points.push(point);
                });

                // `points` arrives in series order, which is back to front —
                // reversed here so the reading in front is read first, as in
                // the legend
                groups.reverse();

                let out = `<span style="font-size: 0.9em">${this.points[0].key}</span>`;

                groups.forEach(function (group) {
                    // a single layer needs no heading: the tab names the one
                    // span it reads
                    if (group.label) {
                        out += `<br/><b>${group.label}</b>`;
                    }
                    group.points.forEach(function (point) {
                        const options = point.series.userOptions;
                        out += `<br/><span style="color: ${options.dotColor}">●</span> `
                            + `${options.metric}: <span style="color: ${options.dotColor}">`
                            + `<b>${point.y} ${options.unit}</b></span>`;
                    });
                });

                return out;
            },
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
