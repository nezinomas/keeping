Highcharts.setOptions({
    colors: [
        "var(--chart-color-0)",
        "var(--chart-color-1)",
        "var(--chart-color-2)",
        "var(--chart-color-3)",
        "var(--chart-color-4)",
        "var(--chart-color-5)",
        "var(--chart-color-6)",
        "var(--chart-color-7)",
        "var(--chart-color-8)",
        "var(--chart-color-9)",
    ]
});

function chartCompare(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
        },
        title: {
            text: ""
        },
        legend: {
            enabled: true,
            backgroundColor: undefined,
        },
        xAxis: {
            min: 0.4,
            max: 10.8,
            tickmarkPlacement: "on",
            categories: chartData.categories,
            labels: {
                rotation: -45,
            }
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        tooltip: {
            shared: true,
            crosshairs: true,
            pointFormat: '<span style="color: {series.color}"><b>{series.name}</b>:</span> {point.y:,.0f}ml<br>',
        },
        plotOptions: {
            area: {
                fillOpacity: 0.4
            }
        },
        series: chartData.serries
    });
};
