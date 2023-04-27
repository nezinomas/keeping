$(function () {
    const chartData = JSON.parse(document.getElementById('chart-expenses-data').textContent);
    // convert data
    for (var key in chartData) {
        chartData[key]['y'] /= 100;
    }

    Highcharts.chart('chart-expenses-container', {
        chart: {
            type: 'column',
        },
        title: {
            text: ''
        },
        xAxis: {
            lineColor: '#000',
            lineWidth: 2,
            type: 'category',
            crosshair: true,
            labels: {
                rotation: -45,
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
                formatter: function () {
                    if (this.value >= 100) { return Highcharts.numberFormat(this.value / 1000, 1) + "k"; }
                    return Highcharts.numberFormat(this.value, 0);
                },
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
            formatter: function () {
                const pcnt = ((this.points[0].y / this.points[0].series.data.map(p => p.y).reduce((a, b) => a + b, 0)) * 100);
                return `
                    <b>${this.points[0].key}</b><br>
                    ${Highcharts.numberFormat(this.points[0].y, 0)}€<br>
                    ${Highcharts.numberFormat(pcnt, 1)}%
                `;
            }
        },
        plotOptions: {
            column: {
                colorByPoint: true,
            }
        },
        series: [{
            data: chartData,
            dataLabels: {
                enabled: true,
                rotation: -90,
                color: '#000',
                align: 'right',
                y: 5,
                style: {
                    fontSize: '10px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false
                },
                formatter: function() {
                    const pcnt = (this.y / this.series.data.map(p => p.y).reduce((a, b) => a + b, 0)) * 100;
                    return Highcharts.numberFormat(pcnt, 1) + '%';
                },
            }
        }]
    });
});
