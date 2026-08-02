function chartOverview(consumptionId, quantityId, containerId) {
    if (Highcharts.seriesTypes.lollipop) {
        Highcharts.seriesTypes.lollipop.prototype.alignDataLabel = Highcharts.Series.prototype.alignDataLabel;
    }

    const consumption = JSON.parse(document.getElementById(consumptionId).textContent);
    const quantity = JSON.parse(document.getElementById(quantityId).textContent);

    const blue = "var(--drinks-data)";

    // fill the page as a hero chart: ~62% of the viewport, clamped so it never
    // gets cramped or absurdly tall
    const viewportH = window.innerHeight || 900;
    const chartHeight = Math.min(760, Math.max(480, Math.round(viewportH * 0.62)));

    // the average is furniture: a level to read the months against, not a
    // verdict. It stays in ink whichever side of the Limit it falls, because the
    // area already turns above the Limit and the Stat Card already says which
    // side it is on
    const avgLineColor = "var(--drinks-ink-muted)";
    const avgTextColor = "var(--drinks-ink-muted)";

    const avgLabelY = (consumption.target - 50 <= consumption.avg && consumption.avg <= consumption.target) ? 15 : -5;
    const targetLabelY = (consumption.avg - 50 <= consumption.target && consumption.target <= consumption.avg) ? 15 : -5;

    const maxQuantity = (quantity.data && quantity.data.length > 0) ? Math.max(...quantity.data) : 0;
    const categoryMax = (consumption.categories && consumption.categories.length > 0) ? consumption.categories.length - 1 : undefined;

    Highcharts.chart(containerId, {
        chart: {
            height: "420px",
        },
        title: {
            text: ""
        },
        legend: {
            enabled: false,
        },
        xAxis: {
            categories: consumption.categories,
            type: "category",
            tickmarkPlacement: "on",
            min: 0.35,
            max: categoryMax - 0.35,
        },
        yAxis: [
            {
                // TOP pane: average daily volume (ml)
                min: 0,
                top: "0%",
                height: "70%",
                title: {
                    text: consumption.text.alcohol,
                },
                plotLines: [
                    {
                        // Secondary x axis baseline at y=0
                        color: "var(--drinks-ink)",
                        width: 1,
                        value: 0,
                        zIndex: 10,
                    },
                    {
                        // the Limit is the one rule that governs a colour: the
                        // area above it turns, so the rule wears the same harm
                        color: "var(--drinks-harm)",
                        width: 1.5,
                        dashStyle: "Dash",
                        value: consumption.target,
                        zIndex: 10,
                        label: Object.assign(
                            drinksRuleLabel(
                                `${consumption.text.limit}: ${consumption.target.toFixed(consumption.decimals)}`,
                                "var(--drinks-harm)",
                                "right"
                            ),
                            // the two rules step apart when they nearly coincide
                            { y: targetLabelY - 8 }
                        )
                    },
                    {
                        color: avgLineColor,
                        width: 1.5,
                        dashStyle: "Dot",
                        value: consumption.avg,
                        zIndex: 11,
                        label: Object.assign(
                            drinksRuleLabel(
                                `Avg: ${consumption.avg.toFixed(consumption.decimals)}`,
                                avgTextColor,
                                "right"
                            ),
                            { y: avgLabelY - 8 }
                        )
                    }
                ],
            },
            {
                // LOW pane: monthly quantity (units)
                min: 0,
                max: maxQuantity > 0 ? maxQuantity : undefined,
                endOnTick: false,
                top: "78%",
                height: "22%",
                offset: 0,
                title: {
                    text: quantity.text.quantity,
                    style: { color: blue },
                },
                labels: {
                    style: { color: blue },
                },
            }
        ],
        tooltip: {
            shared: true,
        },
        series: [
            {
                // TOP: filled area, split-coloured at the limit
                type: "area",
                yAxis: 0,
                opacity: 0.85,
                name: consumption.text.alcohol,
                showInLegend: false,
                data: consumption.data,
                // the zones below colour what is drawn; this is what the series
                // itself is, and it is what the tooltip reads. Without it the
                // series falls back to the first colour in the theme's ramp,
                // which belongs to Year Comparison
                color: "var(--drinks-data)",
                zoneAxis: "y",
                // under the Limit is the baseline reading, so it is the data
                // hue; over it is the only part of the year that gets harm
                zones: [
                    {
                        value: consumption.target,
                        color: "var(--drinks-data)",
                        fillColor: "var(--drinks-data-wash)"
                    },
                    {
                        color: "var(--drinks-harm)",
                        fillColor: "var(--drinks-harm-wash)"
                    }
                ],
                marker: {
                    enabled: true,
                    radius: 2.5,
                    symbol: "circle"
                },
                dataLabels: {
                    enabled: true,
                    verticalAlign: "bottom",
                    y: -8,
                    crop: false,
                    overflow: "allow",
                    style: {
                        fontFamily: "var(--drinks-mono)",
                        fontSize: "10px",
                        color: "var(--drinks-ink)",
                        fontWeight: "400",
                        textOutline: "none",
                    },
                    formatter: function () {
                        return this.y > 0
                            ? Highcharts.numberFormat(this.y, consumption.decimals)
                            : "";
                    },
                },
                tooltip: {
                    // the drink-type dropdown names the unit and its precision.
                    // The series colour, not the point's: the zones colour the
                    // graph rather than the points, so a point has no colour of
                    // its own to read here
                    pointFormat: `${consumption.text.alcohol}: <span style="color: {series.color}"><b>{point.y:,.${consumption.decimals}f} ${consumption.text.unit}</b></span><br>`,
                }
            },
            {
                type: "lollipop",
                yAxis: 1,
                name: quantity.text.quantity,
                data: quantity.data,
                color: blue,
                connectorWidth: 2,
                connectorColor: blue,
                showInLegend: false,
                marker: {
                    enabled: true,
                    symbol: "circle",
                    radius: 5,
                    fillColor: blue,
                    lineWidth: 0,
                },
                dataLabels: {
                    enabled: true,
                    align: "center",
                    verticalAlign: "bottom",
                    y: -8,
                    x: 0,
                    crop: false,
                    overflow: "allow",
                    style: {
                        fontFamily: "var(--drinks-mono)",
                        fontSize: "10px",
                        color: "var(--drinks-ink-muted)",
                        textOutline: "none",
                        fontWeight: "400"
                    },
                    formatter: function () {
                        return this.y > 0 ? Highcharts.numberFormat(this.y, 1) : "";
                    },
                },
                tooltip: {
                    pointFormat: `${quantity.text.quantity}: <span style="color: {series.color}"><b>{point.y:.1f}</b></span><br>`,
                }
            }
        ]
    });
};
