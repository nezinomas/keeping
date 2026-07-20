function chartTrend(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    const plotLines = (chartData.target !== null) ? [
    {
        color: "#333",
        width: 2,
        value: chartData.target,
        zIndex: 10,
        label: {
            text: `${chartData.text.limit}: ${chartData.target.toFixed()}`,
            align: "right",
            x: -5,
            style: {
                color: "#333",
                fontWeight: "bold"
            }
        }
    }] : [];

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
            plotLines: plotLines,
        },
        tooltip: {
            shared: true,
            pointFormat: "{series.name}: <b>{point.y:,.0f} ml</b><br>"
        },
        series: [{
            type: "spline",
            name: chartData.text.r30,
            data: chartData.rolling_30,
            color: "var(--chart-negative-dark)",
            lineWidth: 3,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.r7,
            data: chartData.rolling_7,
            color: "var(--chart-alpha-25)",
            lineWidth: 1,
            marker: {
                enabled: false
            }
        }]
    });
};
