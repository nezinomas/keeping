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


function chartExpenses(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    // convert data
    for(i = 0; i < chartData.data.length; i++) {
        for(y = 0; y < chartData.data[i]["data"].length; y++) {
            chartData.data[i]["data"][y] /= 100
        }
    }

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            zoomType: "x",
            panning: {
                enabled: true,
                type: "x"
            },
            panKey: "shift"
        },
        title: {
            text: "",
        },
        xAxis: {
            categories: chartData.categories,
            crosshair: true,
            gridLineWidth: 0,
        },
        yAxis: {
            title: {
                text: ""
            },
            labels: {
                formatter: function () {
                    if (this.value > 500) {
                        return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    }
                    return Highcharts.numberFormat(this.value, 0);
                },
            }
        },
        tooltip: {
            headerFormat: '<div class="">{point.key}</div>',
            pointFormat:
                '<div class=""><span style="color:{series.color};">{series.name}:</span> ' +
                '<span> <b>{point.y:,.1f}€</b></span></div>',
            footerFormat: "",
            shared: true,
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0,
                borderRadius: 0,
            }
        },
        series: chartData.data,
    });
};
