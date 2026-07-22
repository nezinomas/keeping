function chartConsumption(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    const avg_line_color = (chartData.avg > chartData.target) ? "var(--chart-negative-dark)" : "var(--chart-positive-dark)";
    const avg_text_color = (chartData.avg > chartData.target) ? "var(--chart-negative-super-dark)" : "var(--chart-positive-super-dark)";

    const avg_label_y = (chartData.target - 50 <= chartData.avg && chartData.avg <= chartData.target) ? 15 : -5
    const target_label_y = (chartData.avg - 50 <= chartData.target && chartData.target <= chartData.avg) ? 15 : -5;

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
            plotLines: [
            {
                color: "#333",
                width: 2,
                dashStyle: "Dash",
                value: chartData.target,
                zIndex: 10,
                label: {
                    text: `${chartData.text.limit}: ${chartData.target.toFixed()}`,
                    align: "right",
                    x: -5,
                    y: target_label_y,
                    style: {
                        color: "#333",
                        fontWeight: "bold"
                    }
                }
            },
            {
                color: avg_line_color,
                width: 2,
                value: chartData.avg,
                zIndex: 11,
                label: {
                    text: `Avg: ${chartData.avg.toFixed()}`,
                    align: "right",
                    x: -5,
                    y: avg_label_y,
                    style: {
                        color: avg_text_color,
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
                fillOpacity: 0.85
            },
        },
        series: [{
            type: "area",
            name: chartData.text.alcohol,
            showInLegend: false,
            data: chartData.data,
            // fill down to the baseline, split-coloured at the limit:
            // green below the limit, red above it
            zoneAxis: "y",
            zones: [
                {
                    value: chartData.target,
                    color: "var(--chart-positive-dark)",
                    fillColor: "var(--chart-positive)"
                },
                {
                    color: "var(--chart-negative-dark)",
                    fillColor: "var(--chart-negative)"
                }
            ],
            marker: {
                enabled: true,
                radius: 2.5,
                symbol: "circle"
            }
        }]
    });
};
