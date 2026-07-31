// A recurring-shape profile: one category axis, and the two independent
// questions the Habits tab asks of it — how often a Drink was recorded, and how
// much on the days it was. Drawn for the weekday profile and for the pooled
// typical year, which differ only in what a category is.
function chartDrinksProfile(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // each axis wears its own series' colour, so a reader never has to work out
    // which scale the columns are on and which one the line is on. Declared
    // once here rather than twice, because an axis in one colour and its series
    // in another is worse than neither being coloured at all
    //
    // the columns are the books chart's: a pale tint of --secondary drawn inside
    // a solid line of it. The rate is a backdrop the intensity line is read
    // against, and a solid block of colour competes with the line for attention
    const rateColor = "var(--secondary)";
    const rateFill = "var(--chart-alpha-25)";
    const intensityColor = "var(--chart-color-6)";

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
        },
        title: {
            text: chartData.text.title
        },
        subtitle: {
            // which years a pooled chart is drawn from. The weekday profile
            // reads the one year the tab already names, so it sends none
            text: chartData.text.subtitle || ""
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
            }
        },
        series: [
            {
                type: "column",
                name: chartData.text.share,
                data: chartData.drinking_day_share,
                yAxis: 0,
                color: rateFill,
                borderColor: rateColor,
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
                color: intensityColor,
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
