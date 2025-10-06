function chartConsumption(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    const avg_line_color = (chartData.avg > chartData.target) ? "var(--chart-negative-super-dark)" : "var(--chart-warning-super-dark)";

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
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: "category",
            tickmarkPlacement: "on",
            labels: {
                rotation: -45,
            }
        },
        yAxis: {
            title: {
                text: ""
            },
            min: 0,
            plotLines: [{
                color: "#333",
                width: 2,
                value: chartData.target,
                label: {
                    text: `${chartData.text.limit}: ${chartData.target.toFixed()}`,
                    align: "right",
                    x: -5,
                    y: chartData.target_label_y,
                    style: {
                        color: "#333",
                        fontWeight: "bold"
                    }
                }
            }, {
                color: avg_line_color,
                width: 2,
                value: chartData.avg,
                label: {
                    text: `Avg: ${chartData.avg.toFixed()}`,
                    align: "right",
                    x: -5,
                    y: chartData.avg_label_y,
                    style: {
                        color: avg_line_color,
                        fontWeight: "bold"
                    }
                }
            }],
        },
        tooltip: {
            shared: true,
            pointFormat: "<b>{point.y:,.0f} ml</b><br>"
        },
        plotOptions: {
            area: {
                fillOpacity: 0.25
            },
        },
        series: [{
            type: "area",
            name: chartData.text.alcohol,
            showInLegend: false,
            data: chartData.data,
            threshold: chartData.target,
            color: "var(--chart-negative-super-dark)",
            negativeColor: 'var(--chart-positive-super-dark)',
            dataLabels: {
                enabled: true,
                color: "#000",
                align: "left",
                format: "{point.y:.0f}",
            }
        }]
    });
};
