function chartOverview(consumptionId, quantityId, containerId) {
    const paper = paperTwoPanes();

    const consumption = JSON.parse(document.getElementById(consumptionId).textContent);
    const quantity = JSON.parse(document.getElementById(quantityId).textContent);

    // a level to read the months against, not a verdict: muted on either side of the
    // Limit, as the area and the Stat Card already tell which side it is on
    const avgLineColor = "var(--skin-ink-muted)";

    // without a Drink Target the chart draws no Limit rule and no harm zone
    const limit = consumption.limit;
    const avgLabelY = (limit.is_set && limit.amount - 50 <= consumption.avg && consumption.avg <= limit.amount) ? 15 : -5;
    const targetLabelY = (consumption.avg - 50 <= limit.amount && limit.amount <= consumption.avg) ? 15 : -5;

    const limitRule = limit.is_set ? [{
        // the Limit is the one rule that governs a colour: the
        // area above it turns, so the rule wears the same harm
        color: "var(--skin-harm)",
        width: 1.5,
        dashStyle: "Dash",
        value: limit.amount,
        zIndex: 10,
        label: Object.assign(
            paperRuleLabel(
                `${consumption.text.limit}: ${limit.amount.toFixed(consumption.decimals)}`,
                "harm"
            ),
            // the two rules step apart when they nearly coincide
            { y: targetLabelY - 8 }
        )
    }] : [];

    // under the Limit is the baseline reading, so it is the data
    // hue; over it is the only part of the year that gets harm
    const dataZone = {
        color: "var(--skin-data)",
        fillColor: "var(--skin-data-wash)"
    };
    const zones = limit.is_set
        ? [Object.assign({ value: limit.amount }, dataZone), {
            color: "var(--skin-harm)",
            fillColor: "var(--skin-harm-tint)"
        }]
        : [dataZone];

    Highcharts.chart(containerId, Highcharts.merge(paper.base, {
        xAxis: paper.xAxis(consumption.categories),
        yAxis: [
            Highcharts.merge(paper.paneTop, {
                title: {
                    text: consumption.text.alcohol,
                },
                plotLines: [
                    {
                        color: "var(--skin-ink)",
                        width: 1,
                        value: 0,
                        zIndex: 10,
                    },
                    ...limitRule,
                    {
                        color: avgLineColor,
                        width: 1.5,
                        dashStyle: "Dot",
                        value: consumption.avg,
                        zIndex: 11,
                        label: Object.assign(
                            paperRuleLabel(
                                `Avg: ${consumption.avg.toFixed(consumption.decimals)}`
                            ),
                            { y: avgLabelY - 8 }
                        )
                    }
                ],
            }),
            Highcharts.merge(paper.paneBottom, {
                title: {
                    text: quantity.text.quantity,
                },
            }),
        ],
        series: [
            {
                type: "area",
                yAxis: 0,
                opacity: 0.85,
                name: consumption.text.alcohol,
                showInLegend: false,
                data: consumption.data,
                // the zones colour what is drawn; this is the series' own colour,
                // which the tooltip reads, not the theme ramp's first (Year Comparison's)
                color: "var(--skin-data)",
                zoneAxis: "y",
                zones: zones,
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
                    formatter: function () {
                        return this.y > 0
                            ? Highcharts.numberFormat(this.y, consumption.decimals)
                            : "";
                    },
                },
                tooltip: {
                    // the series colour, not the point's: the zones colour the graph,
                    // not the points; the drink-type dropdown names unit and precision
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
