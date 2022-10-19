$(function () {
    const chartData = JSON.parse(
        document.getElementById('chart-expenses-data').textContent
    );

    Highcharts.chart('chart-expenses-container', {
        chart: {
            type: 'bar',
            height: 485,
        },
        title: {
            text: ''
        },
        subtitle: {
            text: ''
        },
        xAxis: {
            type: 'category',
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                }
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
        plotOptions: {
            series: {
                borderWidth: 0,
                dataLabels: {
                    enabled: true,
                    format: '{point.y:.1f}'
                }
            }
        },
        tooltip: {
            headerFormat: '',
            pointFormat: '{point.name}: <b>{point.y:.1f}</b><br/>',
            style: {
                fontSize: '12px',
                fontFamily: 'Calibri, Verdana',
            }
        },
        series: [
            {
                data: chartData,
                dataLabels: {
                    enabled: true,
                    rotation: 0,
                    color: '#000',
                    align: 'right',
                    format: '{point.y:.1f}', /* one decimal */
                    y: -1,
                    style: {
                        fontSize: '9px',
                        fontWeight: 'bold',
                        fontFamily: 'Verdana, sans-serif',
                        textOutline: false
                    }
                }
            },
        ],
    });
});