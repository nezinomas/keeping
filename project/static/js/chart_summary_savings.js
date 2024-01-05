function annotationLabels(total_list, invested_list, profit_list) {
    total_list.forEach(function (element, index, total_list) {
        let y_val = element;
        if (profit_list[index] < 0) {
            y_val = invested_list[index]
        }
        total_list[index] = {
            point: { xAxis: 0, yAxis: 0, x: index, y: y_val },
            text: Highcharts.numberFormat(element, 0),
        };
    });
    return total_list;
};


function chartSavings(container) {
    const positive = '#548235';
    const negative = '#c0504d';
    const chartData = JSON.parse(document.getElementById(`${container}_data`).textContent);

    // convert data
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
            text: chartData.title,
            style: {
                fontSize: '14px',
            },
        },
        annotations: [{
            draggable: '',
            labelOptions: {
                y: -8,
                useHTML: true,
                crop: false,
                overflow: 'none',
                style: {
                    fontSize: '12px',
                }
            },
            labels: annotationLabels(chartData.total, chartData.invested, chartData.profit)
        }],
        xAxis: {
            categories: chartData.categories,
            lineColor: 'black',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                },
            },
        },
        yAxis: {
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
                },
            },
            plotLines: [{
                color: '#c0c0c0',
                width: 1,
                value: 0,
                zIndex:2
            }],
            stackLabels: {
                enabled: false,
            },
            startOnTick: false,
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
            useHTML: true,
            pointFormat: '{point.y:,.0f}',
            style: {
                fontSize: '12px',
            },
            formatter: function () {
                let {series} = this.series.chart;
                let profit = series[0].yData[this.point.x];
                let invested = series[1].yData[this.point.x];
                let percent = (profit * 100) / invested;
                return `
                    <div><b>${this.x}</b></div>
                    <div class="my-2">${chartData.text_profit}: ${Highcharts.numberFormat(percent, 1)}%</div>
                `
            }
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            column: {
                stacking: 'normal',
            },
        },
        series: [{
            name: chartData.text_profit,
            data: chartData.profit,
            color: '#5D9C59',
            opacity: 0.8,
            borderColor: '#548235',
            borderWidth: '0.5',
            borderRadius: 0,
            dataLabels: {
                enabled: true,
                formatter: function () {
                    let val = Highcharts.numberFormat(this.y, 0)
                    if (val == 0) {
                        return '';
                    } else {
                        let color = (val < 0) ? negative : positive;
                        return `<span style="color:${color};">${val}</span>`;
                    }
                },
                style: {
                    fontWeight: 'bold',
                    textOutline: false,
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
        let series = chartObj.series[0];
        $.each(series.data, function (i, point) {
            if (point.negative) {
                point.color = negative; /* + tooltip border color */
                point.graphic.css({ stroke: negative, color: '#EB5353'});
            }
        });
    });
};
