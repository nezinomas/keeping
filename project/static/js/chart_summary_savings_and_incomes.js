$(function () {
    const chartData = JSON.parse(document.getElementById('chart-data').textContent);

    // convert data
    for (i = 0; i < chartData.categories.length; i++) {
        chartData.incomes[i] /= 100
        chartData.savings[i] /= 100
    }

    Highcharts.chart('chart-container', {
        title: {
            text: chartData.text.title,
        },
        xAxis: {
            categories: chartData.categories,
        },
        yAxis: {
            labels: {
                formatter: function () {
                    return Highcharts.numberFormat(this.value / 1000, 0) + "k";
                },
            },
            title: {
                text: ''
            },
        },
        tooltip: {
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
            borderRadius: '5%',
            states: {
                inactive: {
                    opacity: 1,
                },
            },
            dataLabels: {
                enabled: true,
                x: 3,
                style: {
                    color: 'black',
                    textOutline: false
                },
                formatter: function () {
                    let i = this.series.data.indexOf(this.point);
                    return `${Highcharts.numberFormat(chartData.incomes[i] / 1000, 1)}`;
                },
            }
        }, {
            name: chartData.text.savings,
            data: chartData.savings,
            type: 'line',
            lineWidth: 2,
            marker: {
                lineWidth: 2,
            },
            states: {
                inactive: {
                    opacity: 1,
                },
            },
            dataLabels: {
                enabled: true,
                y: -3,
                x: 4.5,
                style: {
                    fontWeight: 'normal',
                    textOutline: false,
                    color: 'black',
                },
                formatter: function () {
                    let i = this.series.data.indexOf(this.point);
                    return `${Highcharts.numberFormat(chartData.percents[i], 1)}%`;
                },
            }
        }]
    });
});
