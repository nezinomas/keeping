function chartExpensesTarget(idData, idContainer) {
    var chartData = JSON.parse(document.getElementById(idData).textContent);

    // convert targets
    for(var i = 0; i < chartData.target.length; i++) {
        chartData.target[i] /= 100;
    }

    // convert data
    for (var key in chartData.fact) {
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
            opacity: '0.7',
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
                y: -2,
                style: {
                    fontSize: '9px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false,
                },
            },
        }
    ]
    }, function (chartObj) {
        /* align datalabels for expenses that exceeds targets */
        var series = chartObj.series[1];
        $.each(series.data, function (i, point) {
            var max = chartObj.series[0].data[point.x].y;
            var y = point.y;

            max = parseFloat(max.toFixed(1));
            y = parseFloat(y.toFixed(1));

            if (y <= max) {
                var clr = 'green';

                point.dataLabel.css({color: clr });

                point.color = clr;
                point.graphic.attr({ fill: clr });
            }
            else {
                var p = 28;
                if (y < 100) { p = 21; }
                if (y < 10) { p = -2; }

                var clr_bar = 'red';
                var clr_label = '#b4010d';

                if(y <= max * 1.1) {
                    clr_bar = '#ffcc00';
                    clr_label = '#efbf00';
                }

                point.dataLabel.attr({ x: point.dataLabel.x + p });
                point.dataLabel.css({color: clr_label });

                point.color = clr_bar;
                point.graphic.attr({ fill: clr_bar });
            }
        });
    });
};
