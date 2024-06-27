function loadMonthExpensesChart(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // convert data
    for (var key in chartData) {
        chartData[key]['y'] /= 100;
    }

    Highcharts.chart(idContainer, {
        chart: {
            type: 'bar',
            height: 485,
            spacingLeft: 5,
            marginBottom: chartData.length * 2.85,
        },
        title: {
            text: ''
        },
        xAxis: {
            type: 'category',
            gridLineWidth: 0,
            labels: {
                style: {
                    fontWeight: 'bold',
                },
            }
        },
        yAxis: {
            title: {
                text: ''
            },
        },
        plotOptions: {
            series: {
                borderWidth: 0,
                colorByPoint: true,
            }
        },
        tooltip: {
            headerFormat: '',
            pointFormat: '{point.name}: <b>{point.y:.1f}</b>',
        },
        series: [
            {
                data: chartData,
                borderRadius: 0,
                dataLabels: {
                    format: '{point.y:.0f}',
                    enabled: true,
                    color: '#000',
                    align: 'left',
                    y: -0.5,
                    style: {
                        fontWeight: 'bold',
                        textOutline: false
                    }
                }
            },
        ],
    });
};
