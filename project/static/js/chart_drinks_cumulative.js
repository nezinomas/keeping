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
            borderColor: '#ccc',
            pointFormat: "<p><span style='color: {series.color}'>{series.name}: <b>{point.y:,.1f} L</b></span><p>"
        },
        series: [{
            type: "spline",
            name: chartData.text.this_year,
            data: chartData.this_year,
            color: "var(--chart-negative-dark)",
            lineWidth: 3,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.last_year,
            data: chartData.last_year,
            color: "var(--chart-alpha-50)",
            lineWidth: 2,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.target,
            data: chartData.target,
            color: "#000",
            lineWidth: 2,
            marker: {
                enabled: false
            }
        }]
    });
};
