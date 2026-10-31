// A recurring-shape profile: how often a Drink was recorded, and how much on those days.
// Layers arrive back to front, so the selected year draws over the pooled range.
function chartDrinksProfile(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // each axis wears its series' colour, so a reader sees which scale is whose; the
    // rate is a pale backdrop, so a solid block does not compete with the line; a
    // layer behind is paler still and unbordered, so the two never read as one series
    const rateColor = "var(--skin-data)";
    const rateFill = "var(--skin-data-tint)";
    const backRateFill = "var(--skin-data-faint)";
    const backRateBorder = "var(--skin-data-edge)";
    // two measures rather than two spans, so the skin's second hue; not harm, as an
    // Intensity is only read against a threshold
    const intensityColor = "var(--skin-second)";

    // the stat card above prints the whole sentence; a phone's chart fits only the level
    const threshold = chartData.heavy_threshold.toFixed(0);
    const heavyRule = `> ${threshold} ${chartData.text.intensity_unit}`;
    const heavyRuleText = PAPER_WIDE
        ? `${chartData.text.threshold_label}: ${heavyRule}`
        : heavyRule;

    const layers = chartData.layers;
    const series = [];

    layers.forEach(function (layer, index) {
        // the last layer is the reading the chart is about
        const front = index === layers.length - 1;

        // a single layer needs no span: the tab already names its year
        const name = (metric) => layer.label ? `${metric} · ${layer.label}` : metric;

        // two layers share one slot (`grouping` below): the back one full width,
        // the front one narrowed inside it
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
            // the tooltip groups by span, so it needs the metric apart from `name`
            metric: chartData.text.share,
            unit: chartData.text.share_unit,
            layerLabel: layer.label,
            // the axis colour: a 10%-alpha backdrop fill is invisible as a bullet
            dotColor: rateColor,
            valueColor: rateColor,
        });

        series.push({
            type: "line",
            name: name(chartData.text.intensity),
            data: layer.intensity,
            yAxis: 1,
            color: intensityColor,
            // one metric, one hue: only the weight and dash say which span it is
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
            // the bullet is a mark and keeps the hue; the value is text
            valueClass: "chart-tip--second",
        });
    });

    Highcharts.chart(idContainer, {
        chart: {
            // aligned ticks would override the rate axis' tickInterval, and only
            // the rate axis draws gridlines
            alignTicks: false,
        },
        legend: {
            // position comes from chart_paper.js
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            crosshair: true,
        },
        yAxis: [
            {
                // ends at the rate this reader reaches, not a fixed cap: how often a
                // Drink is recorded differs by an order of magnitude between accounts
                title: {
                    text: chartData.text.share_unit,
                    style: { color: rateColor },
                },
                labels: {
                    style: { color: rateColor },
                },
                // a share read off a floating baseline is not a share
                min: 0,
                ceiling: 100,
                tickInterval: 10,
                // padding would push a 29% peak onto the tick after the one it needs
                maxPadding: 0,
            },
            {
                // Std Av, not the dropdown's unit: the rule below is defined in Std Av
                title: {
                    text: chartData.text.intensity_unit,
                    style: { color: "var(--skin-second-ink)" },
                },
                labels: {
                    style: { color: "var(--skin-second-ink)" },
                },
                min: 0,
                opposite: true,
                gridLineWidth: 0,
                plotLines: [
                    {
                        // ink, not harm: a level rather than a verdict, and harm
                        // beside the Intensity's hue would read as a third series
                        color: "var(--skin-ink-muted)",
                        width: 1.5,
                        dashStyle: "Dash",
                        value: chartData.heavy_threshold,
                        zIndex: 5,
                        label: paperRuleLabel(heavyRuleText)
                    }
                ]
            }
        ],
        tooltip: {
            shared: true,
            // the pale rate columns would leave their own colour near invisible
            borderColor: rateColor,
            // one block per span: a span's column and line are two readings of it
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

                // `points` arrives back to front; the front reading goes first, as in
                // the legend
                groups.reverse();

                let out = this.points[0].key;

                groups.forEach(function (group) {
                    // a single layer needs no heading: the tab names its span
                    if (group.label) {
                        out += `<br/><b>${group.label}</b>`;
                    }
                    group.points.forEach(function (point) {
                        const options = point.series.userOptions;
                        let value = `style="color: ${options.valueColor}"`;
                        if (options.valueClass) {
                            value = `class="${options.valueClass}"`;
                        }
                        out += `<br/><span style="color: ${options.dotColor}">●</span> `
                            + `${options.metric}: <span ${value}>`
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
                // the two spans are the same months, so they share one slot rather
                // than read as neighbours compared
                grouping: false,
            }
        },
        series: series
    });
};
