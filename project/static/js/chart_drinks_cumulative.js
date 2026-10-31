function chartDrinksCumulative(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            tickInterval: Math.ceil(chartData.categories.length / 12),
            labels: {
                rotation: -45,
                formatter: function () {
                    // categories are full ISO dates
                    return this.value.slice(5);
                }
            }
        },
        yAxis: {
            title: {
                text: chartData.text.unit
            },
            min: 0,
            // a cumulative curve ends at its maximum: a rounded-up top tick
            // would spend a fifth of the plot on empty sky above it
            endOnTick: false,
            maxPadding: 0.02,
        },
        tooltip: {
            shared: true,
            // no borderColor: the border reads as the series being hovered; the
            // unit comes from the payload, since Std Av is counted, not bottled
            pointFormat: `<span style='color: {series.color}'>{series.name}: <b>{point.y:,.1f} ${chartData.text.unit}</b></span><br/>`
        },
        // this year and last are one measure over two spans: two steps of one hue,
        // the older dashed and paler. The target is a level, not a year, so ink
        series: [{
            type: "spline",
            name: chartData.text.this_year,
            data: chartData.this_year,
            color: "var(--skin-data)",
            lineWidth: 2.5,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.last_year,
            data: chartData.last_year,
            color: "var(--skin-year-0)",
            dashStyle: "ShortDash",
            lineWidth: 2,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.target,
            data: chartData.target,
            color: "var(--skin-ink-muted)",
            dashStyle: "Dot",
            lineWidth: 1.5,
            marker: {
                enabled: false
            }
        }]
    });
};
