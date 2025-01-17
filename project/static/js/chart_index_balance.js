$(function () {
    const chartData = JSON.parse(document.getElementById("chart-balance-data").textContent);
    // convert data
    for(i = 0; i < 12; i++) {
        chartData.incomes[i] /= 100
        chartData.expenses[i] /= 100
    }

    Highcharts.chart("chart-balance-container", {
        chart: {
            marginBottom: 74,
        },
        title: {
            text: "",
        },
        legend: {
            enabled: true,
            backgroundColor: undefined,
        },
        xAxis: {
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: "category",
            tickmarkPlacement: "on",
            labels: {
                rotation: -45,
            },
        },
        yAxis: {
            labels: {
                formatter: function () {
                    if (this.value >= 100) {
                        return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    }
                    return Highcharts.numberFormat(this.value, 0);
                },
            },
            title: {
                text: ""
            },
        },
        tooltip: {
            split: true,
            pointFormat: "{series.name}: <b>{point.y:,.0f}€</b><br>",
        },
        plotOptions: {
            area: {
                fillOpacity: 0.6
            }
        },
        series: [{
            type: "area",
            name: chartData.incomes_title,
            data: chartData.incomes,
            color: "#5D9C59"
        }, {
            type: "area",
            name: chartData.expenses_title,
            data: chartData.expenses,
            color: "#EB5353"
        }]
    });
});
