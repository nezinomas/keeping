$(function () {
    const chartData = JSON.parse(document.getElementById('chart-incomes-types-data').textContent);

    // convert data
    for (i = 0; i < chartData.data.length; i++) {
        for (n = 0; n < chartData.data[i].data.length; n++) {
            chartData.data[i].data[n] /= 100
        }
    }

    Highcharts.chart('chart-incomes-types-container', {
        chart: {
            type: 'column',
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
            categories: chartData.categories,
        },
        yAxis: {
            min: 0,
            title: {
                text: '%'
            },
        },
        tooltip: {
            pointFormat: '<span style="color:{series.color}">{series.name}</span>:  <b>{point.y:,.0f}€</b> ({point.percentage:.1f}%)<br/>',
            shared: true,
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
