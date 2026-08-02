function chartDrinksCumulative(idData, idContainer) {
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
            tickInterval: Math.ceil(chartData.categories.length / 12),
            labels: {
                rotation: -45,
                formatter: function () {
                    // categories are full ISO dates; show only MM-DD on the axis
                    return this.value.slice(5);
                }
            }
        },
        yAxis: {
            title: {
                text: chartData.text.unit
            },
            min: 0,
        },
        tooltip: {
            shared: true,
            // Std Av is counted rather than bottled, so the unit comes from the
            // payload instead of assuming litres
            pointFormat: `<span style='color: {series.color}'>{series.name}: <b>{point.y:,.1f} ${chartData.text.unit}</b></span><br/>`
        },
        // this year and last are the same measure over two spans, so they are
        // two steps of one hue and the older one is dashed as well as paler.
        // The target is furniture: a level, not a year, so it is ink
        series: [{
            type: "spline",
            name: chartData.text.this_year,
            data: chartData.this_year,
            color: "var(--drinks-data)",
            lineWidth: 2.5,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.last_year,
            data: chartData.last_year,
            color: "var(--drinks-data-soft)",
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
            color: "var(--drinks-ink-muted)",
            dashStyle: "Dot",
            lineWidth: 1.5,
            marker: {
                enabled: false
            }
        }]
    });
};
