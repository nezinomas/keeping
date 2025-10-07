function chart_drinks_summary(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            marginBottom: 67,
        },
        title: {
            text: chartData.text.title,
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: "category",
            tickmarkPlacement: "on",
        },
        yAxis: [{
            labels: {
                format: "{value:.0f}",
                style: {
                    color: "var(--chart-negative)",
                },
            },
            title: {
                text: "",
                style: {
                    color: "var(--chart-negative)",
                }
            },
        }, {
            opposite: true,
            labels: {
                format: "{value:.0f}",
                style: {
                    color: "var(--chart-negative-super-dark)",
                },
            },
            title: {
                text: "",
                style: {
                    color: "var(--chart-negative-super-dark)",
                }
            },
        }],
        tooltip: {
            pointFormat: "<b>{point.y:,.0f} ml</b><br>",
        },
        series: [{
            name: chartData.text.per_day,
            yAxis: 0,
            data: chartData.data_ml,
            color: "var(--chart-negative)",
            type: "area",
            marker: {
                fillColor: '#FFFFFF',
                lineWidth: 2,
                lineColor: null // inherit from series
            },
            dataLabels: {
                enabled: true,
                format: "{point.y:.0f}",
                y: -25,
                verticalAlign:"top",
                color: "var(--chart-negative-super-dark)",
                style: {
                    textOutline: 0,
                },
            },
            enableMouseTracking: false,
            fillOpacity: 0.65,
        }, {
            name: chartData.text.per_year,
            yAxis: 1,
            data: chartData.data_alcohol,
            color: "var(--chart-negative-super-dark)",
            type: "line",
            dataLabels: {
                enabled: true,
                format: "{point.y:.1f}",
                y: 25,
                color: "var(--chart-negative-super-dark)",
                style: {
                    textOutline: 0,
                },
            },
            enableMouseTracking: false,
        }],
    });
};
