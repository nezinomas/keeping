function chartDrinksCumulative(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
        },
        title: {
            text: ""
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
            }
        },
        yAxis: {
            title: {
                text: ""
            },
            min: 0,
        },
        tooltip: {
            shared: true,
            pointFormat: "{series.name}: <b>{point.y:,.0f} ml</b><br>"
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
            color: "#333",
            lineWidth: 2,
            dashStyle: 'Dash',
            marker: {
                enabled: false
            }
        }]
    });
};
