function chartOverview(consumptionId, quantityId, containerId) {
    if (Highcharts.seriesTypes.lollipop) {
        Highcharts.seriesTypes.lollipop.prototype.alignDataLabel = Highcharts.Series.prototype.alignDataLabel;
    }

    const consumption = JSON.parse(document.getElementById(consumptionId).textContent);
    const quantity = JSON.parse(document.getElementById(quantityId).textContent);

    const blue = "var(--secondary)";

    // fill the page as a hero chart: ~62% of the viewport, clamped so it never
    // gets cramped or absurdly tall
    const viewportH = window.innerHeight || 900;
    const chartHeight = Math.min(760, Math.max(480, Math.round(viewportH * 0.62)));

    const avgLineColor = (consumption.avg > consumption.target) ? "var(--chart-negative-dark)" : "var(--chart-positive-dark)";
    const avgTextColor = (consumption.avg > consumption.target) ? "var(--chart-negative-super-dark)" : "var(--chart-positive-super-dark)";

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
            labels: {
                rotation: -45,
            }
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
                        color: "#000",
                        width: 2,
                        value: 0,
                        zIndex: 10,
                    },
                    {
                        color: "#333",
                        width: 2,
                        value: consumption.target,
                        zIndex: 10,
                        label: {
                            text: `${consumption.text.limit}: ${consumption.target.toFixed(consumption.decimals)}`,
                            align: "right",
                            x: -5,
                            y: targetLabelY,
                            style: { color: "#333", fontWeight: "bold" }
                        }
                    },
                    {
                        color: avgLineColor,
                        width: 2,
                        value: consumption.avg,
                        zIndex: 11,
                        label: {
                            text: `Avg: ${consumption.avg.toFixed(consumption.decimals)}`,
                            align: "right",
                            x: -5,
                            y: avgLabelY,
                            style: { color: avgTextColor, fontWeight: "bold" }
                        }
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
                zoneAxis: "y",
                zones: [
                    {
                        value: consumption.target,
                        color: "var(--chart-positive-dark)",
                        fillColor: "var(--chart-positive)"
                    },
                    {
                        color: "var(--chart-negative-dark)",
                        fillColor: "var(--chart-negative)"
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
                        fontSize: "0.66rem",
                        color: "#3a3a3a",
                        fontWeight: "bold",
                        textOutline: "none",
                    },
                    formatter: function () {
                        return this.y > 0
                            ? Highcharts.numberFormat(this.y, consumption.decimals)
                            : "";
                    },
                },
                tooltip: {
                    // the drink-type dropdown names the unit and its precision
                    pointFormat: `${consumption.text.alcohol}: <b>{point.y:,.${consumption.decimals}f} ${consumption.text.unit}</b><br>`,
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
                        fontSize: "0.62rem",
                        color: "#000",
                        textOutline: "none",
                        fontWeight: "bold"
                    },
                    formatter: function () {
                        return this.y > 0 ? Highcharts.numberFormat(this.y, 1) : "";
                    },
                },
                tooltip: {
                    pointFormat: `${quantity.text.quantity}: <b>{point.y:.1f}</b><br>`,
                }
            }
        ]
    });
};
