$(function () {
    const chartData = JSON.parse(document.getElementById('chart-data').textContent);

    // convert data
    for (i = 0; i < chartData.categories.length; i++) {
        chartData.incomes[i] /= 100
        chartData.savings[i] /= 100
    }

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart('chart-container', {
        title: {
            text: chartData.text.title,
            style: {
                fontSize: '14px',
            }
        },
        xAxis: {
            categories: chartData.categories,
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                },
            },
        },
        yAxis: {
            labels: {
                formatter: function () {
                    return Highcharts.numberFormat(this.value / 1000, 0) + "k";
                },
                style: {
                    fontSize: '10px',
                },
            },
            title: {
                text: ''
            },
        },
        tooltip: {
            useHTML: true,
            style: {
                fontSize: '12px',
            },
            formatter: function () {
                let i = this.series.data.indexOf(this.point);
                return `
                    <table class="hightcharts-tooltip">
                    <tr><td class="head" colspan="2"><b>${this.x}</b></td></tr>
                    <tr><td>${chartData.text.incomes}:</td><td>${Highcharts.numberFormat(chartData.incomes[i], 0)}€</td></tr>
                    <tr><td>${chartData.text.savings}:</td><td>${Highcharts.numberFormat(chartData.savings[i], 0)}€</td></tr>
                    <tr><td>${chartData.text.percents}:</td><td>${Highcharts.numberFormat(chartData.percents[i], 1)}%</td></tr>
                    </table>
                `
            }
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0
            }
        },
        series: [{
            name: chartData.text.incomes,
            data: chartData.incomes,
            opacity: 0.85,
            type: 'column',
            color: Highcharts.getOptions().colors[2],
            borderRadius: '5%',
            states: {
                inactive: {
                    opacity: 1,
                },
            },
        }, {
            name: chartData.text.savings,
            data: chartData.savings,
            type: 'line',
            lineWidth: 2,
            color: Highcharts.getOptions().colors[3],
            marker: {
                lineWidth: 2,
                lineColor: Highcharts.getOptions().colors[3],
                fillColor: 'white'
            },
            states: {
                inactive: {
                    opacity: 1,
                },
            },
            dataLabels: {
                enabled: true,
                style: {
                    fontFamily: 'Calibri, sans-serif',
                    fontSize: '12px',
                    fontWeight: 'normal',
                    textOutline: false
                },
                formatter: function () {
                    let i = this.series.data.indexOf(this.point);
                    return `${Highcharts.numberFormat(chartData.percents[i], 1)}%`;
                },
            }
        }]
    });
});
