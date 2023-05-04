function chartExpensesTarget(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // convert targets
    for(i = 0; i < chartData.target.length; i++) {
        chartData.target[i] /= 100;
    }

    // convert data
    for (key in chartData.fact) {
        chartData.fact[key]['y'] /= 100;
        chartData.fact[key]['target'] /= 100;
    }

    Highcharts.chart(idContainer, {
        chart: {
            type: 'bar',
            height: '485'
        },
        title: {
            text: ''
        },
        xAxis: {
            categories: chartData.categories,
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '11px',
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
            }
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            bar: {
                grouping: false,
                shadow: false,
            },
        },
        series: [{
            name: chartData.targetTitle,
            type: 'bar',
            color: 'rgba(0,0,0,0.07)',
            data: chartData.target,
            pointWidth: 19,
            dataLabels: {
                enabled: true,
                rotation: 0,
                color: '#000',
                x: -3,
                y: -15,
                format: '{point.y:.0f}', /* one decimal */
                style: {
                    fontSize: '7px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false
                }
            }
        }, {
            name: chartData.factTitle,
            type: 'bullet',
            data: chartData.fact,
            pointWidth: 13,
            borderRadius: 0,
            targetOptions: {
                borderWidth: 0,
                height: 2,
                color: 'black',
                width: '200%'
            },
            dataLabels: {
                format: '{point.y:.0f}',
                enabled: true,
                rotation: 0,
                align: 'right',
                y: -0.5,
                style: {
                    fontSize: '11px',
                    fontWeight: 'bold',
                    fontFamily: 'Calibri, sans-serif',
                    textOutline: false,
                },
            },
        }
    ]
    }, function (chartObj) {
        /* align datalabels for expenses that exceeds targets */
        $.each(chartObj.series[1].data, function (i, point) {
            let max = chartObj.series[0].data[point.x].y;
            let {y} = point;

            max = parseFloat(max.toFixed(1));
            y = parseFloat(y.toFixed(1));

            if (y <= max) {
                color = '#00e272';
            }
            else {
                p = 28;
                if (y < 100) { p = 21; }
                if (y < 10) { p = -2; }
                point.dataLabel.attr({ x: point.dataLabel.x + p });

                color = (y <= max * 1.1) ? '#feb56a' : '#fa4b42';
            }
            point.color = color;
            point.graphic.attr({ fill: color });
        });
    });
};
