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
        },
        tooltip: {
            pointFormat: "<p>{series.name}: <b>{point.y}</b></p>"
        },
        series: [{
            name: chartData.text.heavy,
            data: chartData.data,
            color: "var(--chart-negative-dark)",
        }]
    });
};
