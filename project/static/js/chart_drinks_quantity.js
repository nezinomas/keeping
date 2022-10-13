$(function () {
    const chartData = JSON.parse(
        document.getElementById('chart-quantity-data').textContent
    );

    Highcharts.chart('chart-quantity-container', {
        chart: {
            type: 'column',
            height: '350px',
        },
        title: {
            text: ''
        },
        xAxis: {
            categories: chartData.categories,
            type: 'category',
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
                rotation: -45,
            }
        },
        yAxis: {
            title: {
                text: ''
            },
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                }
            }
        },
        legend: {
            enabled: false
        },
        tooltip: {
            shared: true,
            headerFormat: '',
            pointFormat: '{series.name}: <b>{point.y:.1f}</b><br/>',
            style: {
                fontSize: '12px',
                fontFamily: 'Calibri, Verdana',
            }
        },
        plotOptions: {
            bar: {
                grouping: false,
                shadow: false,
                pointWidth: 13,
            }
        },
        series: [{
            name: chartData.text.quantity,
            color: 'rgba(70, 171, 157,0.65)',
            borderColor: 'rgba(70, 171, 157, 1)',
            data: chartData.data,
            pointPadding: 0,
            pointPlacement: 0,
            dataLabels: {
                enabled: true,
                rotation: 0,
                color: '#000',
                format: '{point.y:.1f}',
                style: {
                    fontSize: '9px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false
                }
            }
        }]
    });
});
