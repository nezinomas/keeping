document.addEventListener('DOMContentLoaded', () => {
    const chartData = JSON.parse(document.getElementById("chart-incomes-data").textContent);

    // convert data
    for (i = 0; i < chartData.incomes.length; i++) {
        chartData.incomes[i] /= 100
        chartData.salary[i] /= 100
    }

    Highcharts.chart("chart-incomes-container", {
        chart: {
            spacingRight: 25,
        },
        title: {
            text: chartData.chart_title,
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
            pointFormat: "<b>{point.y:,.0f}</b><br>",
        },
        plotOptions: {
            area: {
                dataLabels: {
                    enabled: true,
                    format: "{point.y:,.0f}",
                    verticalAlign:"top",
                    color: "var(--positive-text)",
                    style: {
                        textOutline: 0,
                    },
                },
                enableMouseTracking: false,
                fillOpacity: 0.6,
            },
            line: {
                dataLabels: {
                    enabled: true,
                    format: "{point.y:,.0f}",
                    y: -5,
                    color: "var(--positive-text)",
                    style: {
                        textOutline: 0,
                    },
                },
                enableMouseTracking: false,
            }
        },
        series: [{
            name: chartData.salary_title,
            data: chartData.salary,
            type: "area",
            color: "var(--chart-positive-dark)",
            marker: {
                fillColor: '#FFFFFF',
                lineWidth: 2,
                lineColor: null // inherit from series
            }
        }, {
            name: chartData.incomes_title,
            data: chartData.incomes,
            type: "line",
            lineWidth: 2,
            color: "var(--chart-positive-super-dark)",
        }],
    });
});
