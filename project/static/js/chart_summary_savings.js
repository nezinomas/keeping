function annotationLabels(list) {
    list.forEach(function (element, index, list) {
        var val = Math.round(element);
        list[index] = {
            point: {xAxis: 0, yAxis:0, x: index, y: val},
            text: Highcharts.numberFormat(val, 0),
        };
    });
    return list;
};

function chartSavings(container) {
    const chartData = JSON.parse(document.getElementById(`${container}_data`).textContent);

    // convert data
    chartData.max /= 100;
    for (i = 0; i < chartData.categories.length; i++) {
        chartData.invested[i] /= 100;
        chartData.profit[i] /= 100;
        chartData.total[i] /= 100;
    }

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart(container, {
        chart: {
            type: 'column',
            spacingRight: 25,
        },
        title: {
            text: chartData.chart_title,
            style: {
                fontSize: '16px',
                fontFamily: 'Calibri, Verdana',
                fontWeight: 'bold',
            },
        },
        annotations: [{
            draggable: '',
            labelOptions: {
                y: -8,
            },
            labels: annotationLabels(chartData.total)
        }],
        xAxis: {
            categories: chartData.categories,
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
        },
        yAxis: {
            max: chartData.max,
            title: {
                text: ''
            },
            labels: {
                enabled: true,
                formatter: function () {
                    if (this.value >= 100 || this.value <= 100) {
                        return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    }
                    return Highcharts.numberFormat(this.value, 0);
                },
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
            stackLabels: {
                enabled: false,
            }
        },
        legend: {
            layout: 'horizontal',
            align: 'right',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 0,
            x: -10,
            y: -5,
        },
        tooltip: {
            pointFormat: '{point.y:,.0f}',
            formatter: function () {
                var sum = 0;
                var series = this.series.chart.series;
                for (i in [1,2]) {
                    sum += series[i].yData[this.point.x];
                }
                return '<b>' + this.x + '</b><br/>' +
                    `${this.series.name}: ${Highcharts.numberFormat(this.point.y, 0)}€<br/>` +
                    `${chartData.text_total}: ${Highcharts.numberFormat(sum, 0)}€`;
            }
        },
        plotOptions: {
            column: {
                stacking: 'normal',
            },
        },
        series: [{
            name: chartData.text_profit,
            data: chartData.profit,
            color: 'rgba(84,130,53,0.5)',
            borderColor: '#548235',
            borderWidth: '0.5',
            borderRadius: 0,
            dataLabels: {
                enabled: true,
                formatter: function () {
                    if (this.y == 0) {
                        return '';
                    } else {
                        return `${Highcharts.numberFormat(this.y, 0)}`;
                    }
                },
                style: {
                    fontWeight: 'bold',
                    textOutline: false,
                    color: '#548235'
                },
            }
        }, {
            name: chartData.text_invested,
            data: chartData.invested,
            color: 'rgba(222,176,40,0.5)',
            borderColor: '#bf8f00',
            borderWidth: '0.5',
            borderRadius: 0,
            dataLabels: {
                enabled: true,
                verticalAlign: 'top',
                formatter: function () {
                    return `${Highcharts.numberFormat(this.y, 0)}`;
                },
                style: {
                    fontWeight: 'bold',
                    textOutline: false,
                    color: '#bf8f00'
                },
            }
        }]
    }, function (chartObj) {
        // paint in red negative profit
        var series = chartObj.series[0];
        $.each(series.data, function (i, point) {
                if (point.negative) {
                var c = '#c0504d';
                point.color = c; /* + tooltip border color */
                point.graphic.css({stroke: c, color: 'rgba(192,80,77,0.5)'});
                point.dataLabel.css({ color: c });
            }
        });
    });
};
