function chartDrinksHeavyDays(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            height: "350px",
        },
        title: {
            text: chartData.text.title
        },
        subtitle: {
            text: `${chartData.text.threshold_label}: > ${chartData.heavy_threshold.toFixed()} Std Av`
        },
        legend: {
            enabled: false,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
        },
        yAxis: {
            title: {
                text: chartData.text.unit
            },
            min: 0,
            allowDecimals: false,
            plotBands: [
                { from: 0, to: chartData.low_risk, color: "rgba(76, 175, 80, 0.10)" },
                { from: chartData.low_risk, to: chartData.high_risk, color: "rgba(255, 193, 7, 0.12)" },
                { from: chartData.high_risk, to: Number.MAX_VALUE, color: "rgba(244, 67, 54, 0.12)" }
            ],
            plotLines: [{
                color: "#333",
                width: 2,
                value: chartData.low_risk,
                zIndex: 5,
                label: {
                    text: `${chartData.text.guideline}: ${chartData.low_risk.toFixed(0)}`,
                    align: "right",
                    x: -5,
                    style: {
                        color: "#333",
                        fontWeight: "bold"
                    }
                }
            }]
        },
        tooltip: {
            pointFormat: "<span>{series.name}: <b>{point.y}</b></span><br/>"
        },
        series: [{
            name: chartData.text.heavy,
            data: chartData.data,
            color: "var(--chart-negative-dark)",
        }]
    });
};
