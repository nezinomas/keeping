function chartOverview(consumptionId, quantityId, containerId) {
    const paper = paperTwoPanes();

    const consumption = JSON.parse(document.getElementById(consumptionId).textContent);
    const quantity = JSON.parse(document.getElementById(quantityId).textContent);

    // the average is furniture: a level to read the months against, not a
    // verdict. It stays in ink whichever side of the Limit it falls, because the
    // area already turns above the Limit and the Stat Card already says which
    // side it is on
    const avgLineColor = "var(--skin-ink-muted)";
    const avgTextColor = "var(--skin-ink-muted)";

    const avgLabelY = (consumption.target - 50 <= consumption.avg && consumption.avg <= consumption.target) ? 15 : -5;
    const targetLabelY = (consumption.avg - 50 <= consumption.target && consumption.target <= consumption.avg) ? 15 : -5;

    Highcharts.chart(containerId, Highcharts.merge(paper.base, {
        xAxis: paper.xAxis(consumption.categories),
        yAxis: [
            Highcharts.merge(paper.paneTop, {
                // TOP pane: average daily volume (ml)
                title: {
                    text: consumption.text.alcohol,
                },
                plotLines: [
                    {
                        // Secondary x axis baseline at y=0
                        color: "var(--skin-ink)",
                        width: 1,
                        value: 0,
                        zIndex: 10,
                    },
                    {
                        // the Limit is the one rule that governs a colour: the
                        // area above it turns, so the rule wears the same harm
                        color: "var(--skin-harm)",
                        width: 1.5,
                        dashStyle: "Dash",
                        value: consumption.target,
                        zIndex: 10,
                        label: Object.assign(
                            paperRuleLabel(
                                `${consumption.text.limit}: ${consumption.target.toFixed(consumption.decimals)}`,
                                "var(--skin-harm)"
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
                            paperRuleLabel(
                                `Avg: ${consumption.avg.toFixed(consumption.decimals)}`,
                                avgTextColor
                            ),
                            { y: avgLabelY - 8 }
                        )
                    }
                ],
            }),
            Highcharts.merge(paper.paneBottom, {
                // LOW pane: monthly quantity (units)
                title: {
                    text: quantity.text.quantity,
                },
            }),
        ],
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
                color: "var(--skin-data)",
                zoneAxis: "y",
                // under the Limit is the baseline reading, so it is the data
                // hue; over it is the only part of the year that gets harm
                zones: [
                    {
                        value: consumption.target,
                        color: "var(--skin-data)",
                        fillColor: "var(--skin-data-wash)"
                    },
                    {
                        color: "var(--skin-harm)",
                        fillColor: "var(--skin-harm-wash)"
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
                    style: paper.readingDataLabelStyle,
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
            Highcharts.merge(paper.bottomBars, {
                name: quantity.text.quantity,
                data: quantity.data,
                tooltip: {
                    pointFormat: `${quantity.text.quantity}: <span style="color: {series.color}"><b>{point.y:.1f}</b></span><br>`,
                }
            }),
        ]
    }));
};
