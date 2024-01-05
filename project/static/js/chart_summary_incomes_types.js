$(function () {
    const chartData = JSON.parse(document.getElementById('chart-incomes-types-data').textContent);

    // convert data
    for (i = 0; i < chartData.data.length; i++) {
        for (n = 0; n < chartData.data[i].data.length; n++) {
            chartData.data[i].data[n] /= 100
        }
    }

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart('chart-incomes-types-container', {
        chart: {
            type: 'column',
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
            categories: chartData.categories,
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                },
            },
        },
        yAxis: {
            min: 0,
            title: {
                text: '%'
            },
            labels: {
                style: {
                    fontSize: '10px',
                },
            },
        },
        tooltip: {
            pointFormat: '<span style="color:{series.color}">{series.name}</span>:  <b>{point.y:.0f}€</b> ({point.percentage:.1f}%)<br/>',
            shared: true,
            backgroundColor: '#F0F0F4',
        },
        plotOptions: {
            column: {
                stacking: 'percent',
                dataLabels: {
                    enabled: true,
                    format: '{point.percentage:.1f}%',
                    style: {
                        fontWeight: 'normal',
                        textOutline: 'none',
                    }
                }
            }
        },
        series: chartData.data,
    });
});
