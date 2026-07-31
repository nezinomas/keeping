function chartDrinksWeekday(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

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
                // a share of the times that one weekday has come round, so it
                // has a ceiling: letting the axis auto-scale past 100 would
                // make a Saturday drunk on every week look like there is room
                // above it
                title: {
                    text: chartData.text.share_unit
                },
                min: 0,
                max: 100,
            },
            {
                // Std Av, deliberately not the drink-type dropdown's unit: the
                // plot line below is defined in Std Av, and a converted series
                // would leave it marking a level the columns no longer measure
                title: {
                    text: chartData.text.intensity_unit
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
                borderWidth: 0,
                borderRadius: 4,
                groupPadding: 0.1,
            }
        },
        series: [
            {
                type: "column",
                name: chartData.text.share,
                data: chartData.drinking_day_share,
                yAxis: 0,
                color: "var(--chart-color-0)",
                tooltip: {
                    valueSuffix: ` ${chartData.text.share_unit}`
                },
            },
            {
                // the two series answer different questions — how often, and
                // how much when — so each carries its own axis and its own unit
                // in the tooltip, and neither is readable off the other's scale
                type: "line",
                name: chartData.text.intensity,
                data: chartData.intensity,
                yAxis: 1,
                color: "var(--chart-color-6)",
                lineWidth: 2,
                marker: {
                    enabled: true,
                    radius: 4,
                    symbol: "circle",
                },
                tooltip: {
                    valueSuffix: ` ${chartData.text.intensity_unit}`
                },
            }
        ]
    });
};
