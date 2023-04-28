$(function () {
    const chartData = JSON.parse(document.getElementById('chart-balance-data').textContent);
    // convert data
    for(i = 0; i < 12; i++) {
        chartData.incomes[i] /= 100
        chartData.expenses[i] /= 100
    }

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart('chart-balance-container', {
        chart: {
            marginBottom: 67,
        },
        title: {
            text: '',
        },
        legend: {
            layout: 'horizontal',
            align: 'right',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 0,
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
            split: true,
            pointFormat: '{series.name}: <b>{point.y:,.0f} €</b><br/>',
                style: {
                    fontSize: '13px',
                    fontFamily: 'Calibri, Verdana',
                },
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            area: {
                fillOpacity: 0.5
            }
        },
        series: [{
            type: 'area',
            name: chartData.incomes_title,
            data: chartData.incomes,
            color: '#77933c'
        }, {
            type: 'area',
            name: chartData.expenses_title,
            data: chartData.expenses,
            color: '#c0504d'
        }]
    });
});
