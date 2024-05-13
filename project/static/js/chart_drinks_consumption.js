function chartConsumption(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            height: '350px',
        },
        title: {
            text: ''
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: 'category',
            tickmarkPlacement: 'on',
            labels: {
                rotation: -45,
            }
        },
        yAxis: {
            title: {
                text: ''
            },
            plotLines: [{
                color: '#04a41f',
                width: 2,
                value: chartData.target,
                label: {
                    text: `${chartData.text.limit}: ${chartData.target.toFixed()}`,
                    align: 'right',
                    x: -5,
                    y: chartData.target_label_y,
                    style: {
                        color: '#04a41f',
                        fontWeight: 'bold'
                    }
                }
            }, {
                color: '#ffc000',
                width: 2,
                value: chartData.avg,
                label: {
                    text: `Avg: ${chartData.avg.toFixed()}`,
                    align: 'right',
                    x: -5,
                    y: chartData.avg_label_y,
                    style: {
                        color: '#ffc000',
                        fontWeight: 'bold'
                    }
                }
            }],
        },
        tooltip: {
            shared: true,
            pointFormat: '<b>{point.y:,.0f} ml</b><br>'
        },
        plotOptions: {
            area: {
                fillOpacity: 0.4
            }
        },
        series: [{
            type: 'area',
            name: chartData.text.alcohol,
            showInLegend: false,
            data: chartData.data,
            color: '#c0504d',
                dataLabels: {
                enabled: true,
                color: '#000',
                align: 'left',
                format: '{point.y:.0f}',
                style: {
                    fontSize: '12px',
                    fontWeight: 'bold',
                    fontFamily: 'Calibri, sans-serif',
                    textOutline: false
                }
            }
        }]
    });
};
