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
            plotLines: plotLines,
        },
        tooltip: {
            shared: true,
            borderColor: '#ccc',
            pointFormat: "<p><span style='color: {series.color}'>{series.name}: <b>{point.y:,.0f} ml</b></span></p>"
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
            color: "#0691ff",
            opacity: 0.5,
            lineWidth: 1,
            marker: {
                enabled: false
            }
        }]
    });
};
