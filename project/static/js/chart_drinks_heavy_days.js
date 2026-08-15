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
            pointFormat: '{series.name}: <span style="color: {series.color}"><b>{point.y}</b></span><br/>'
        },
        series: [{
            name: chartData.text.heavy,
            data: chartData.data,
            // every bar here is a count of Heavy days, so the whole series is
            // harm — there is no reading on this chart that is not
            color: "var(--skin-harm)",
            borderWidth: 0,
        }]
    });
};
