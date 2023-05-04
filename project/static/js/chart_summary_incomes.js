$(function () {
    const chartData = JSON.parse(document.getElementById('chart-incomes-data').textContent);

    // convert data
    for (i = 0; i < chartData.incomes.length; i++) {
        chartData.incomes[i] /= 100
        chartData.salary[i] /= 100
    }

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart('chart-incomes-container', {
        chart: {
            spacingRight: 25,
        },
        title: {
            text: chartData.chart_title,
            style: {
                fontSize: '14px',
            }
        },
        legend: {
            layout: 'horizontal',
            align: 'right',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 0,
            x: -10
        },
        xAxis: {
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: 'category',
            lineColor: '#000',
            lineWidth: 2,
            gridLineWidth: 1,
            tickmarkPlacement: 'on',
            labels: {
                style: {
                    fontSize: '10px',
                },
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
                style: {
                    fontSize: '10px',
                },
            },
            title: {
                text: ''
            },

        },
        tooltip: {
            pointFormat: '<b>{point.y:,.0f}</b><br/>',
                style: {
                    fontSize: '12px',
                },
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            area: {
                dataLabels: {
                    enabled: true,
                    format: '{point.y:,.0f}',
                    verticalAlign:'top',
                    color: '#77933c',
                    style: {
                        textOutline: 0,
                    },
                },
                enableMouseTracking: false,
                fillOpacity: 0.65,
            },
            line: {
                dataLabels: {
                    enabled: true,
                    format: '{point.y:,.0f}',
                    y: -5,
                    color: '#2d5f2e',
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
            type: 'area',
            color: '#98bc62',
        }, {
            name: chartData.incomes_title,
            data: chartData.incomes,
            type: 'line',
            color: '#2d5f2e',
        }],
    });
});
