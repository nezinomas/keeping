$(function () {
    const chartData = JSON.parse(
        document.getElementById('chart-incomes-data').textContent
    );

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
                    fontFamily: 'Calibri, Verdana',
                },
            },
        },
        yAxis: {
            labels: {
                formatter: function () {
                    if (this.value >= 100) return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    return Highcharts.numberFormat(this.value, 0);
                },
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
            title: {
                text: ''
            },

        },
        tooltip: {
            pointFormat: '<b>{point.y:,.0f}</b><br/>',
                style: {
                    fontSize: '13px',
                    fontFamily: 'Calibri, Verdana',
                },
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
