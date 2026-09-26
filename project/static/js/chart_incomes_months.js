// amounts arrive in euro
function chartIncomesMonths(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            height: "350px",
        },
        title: {
            text: "",
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
        },
        yAxis: {
            title: {
                text: "",
            },
            labels: {
                format: "{value:,.0f} €",
            },
        },
        tooltip: {
            shared: true,
            valueDecimals: 2,
            valueSuffix: " €",
        },
        series: chartData.series.map(function (series, index) {
            return Object.assign({}, series, {
                color: index === 0 ? "var(--skin-year-0)" : "var(--skin-year-5)",
                borderWidth: 0,
                borderRadius: 0,
            });
        }),
    });
}
