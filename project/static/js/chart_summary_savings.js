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

    Highcharts.chart(container, {
        chart: {
            type: 'column',
            spacingRight: 25,
        },
        title: {
            text: chartData.title,
        },
        xAxis: {
            categories: chartData.categories,
            crosshair: true,
            gridLineWidth: 0,
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
            },
            plotLines: [{
                color: '#c0c0c0',
                width: 1,
                value: 0,
                zIndex:2
            }],
            stackLabels: {
                enabled: true,
                align: 'center',
                // overflow: 'none',
                // borderRadius: 5,
                // backgroundColor: 'rgba(252, 255, 197, 0.7)',
                // borderWidth: 1,
                // borderColor: '#AAA',
                // y: -8,
                formatter: function() {
                  let sum = 0;
                  let {series} = this.axis;
                  let ii = this.x;
                  for (var i in series) {
                    if (series[i].visible && series[i].options.stacking == 'normal') {
                      sum += series[i].yData[this.x];
                    }
                  }
                  if (this.total > 0) {
                    return Highcharts.numberFormat(chartData.total[ii], 0);
                  } else {
                    return '';
                  }
                }
              },
            // startOnTick: false,
        },
        tooltip: {
            pointFormat: '{point.y:,.0f}',
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
            } else {
                point.update({})
            }
        });
    });
};
