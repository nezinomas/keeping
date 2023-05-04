function chartExpensesOnly(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // convert data
    for (var key in chartData) {
        chartData[key]['y'] /= 100;
    }

    Highcharts.chart(idContainer, {
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
        credits: {
            enabled: false
        },
        plotOptions: {
            series: {
                borderWidth: 0,
                colorByPoint: true,
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
                borderRadius: 0,
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
};
