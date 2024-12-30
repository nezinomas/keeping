loadChart('chart-expenses-data', 'chart-expenses-container');

function loadChart(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    let max_category_len = 0;

    // convert data
    for (var key in chartData) {
        chartData[key]['y'] /= 100;

        if (chartData[key]['name'].length > max_category_len) {
            max_category_len = chartData[key]['name'].length;
        }
    }

    Highcharts.chart(idContainer, {
        chart: {
            type: 'bar',
            height: 485,
            marginLeft: max_category_len * 6.55,
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