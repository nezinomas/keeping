$(function () {
    const chartData = JSON.parse(
        document.getElementById('chart-expenses-data').textContent
    );

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
                var rtn = '';
                var pcnt = ((this.points[0].y / this.points[0].series.data.map(p => p.y).reduce((a, b) => a + b, 0)) * 100);
                rtn = '<b>' + this.points[0].key + '</b>';
                rtn += '<br>' + Highcharts.numberFormat(this.points[0].y, 0) + '€<br>';
                rtn += Highcharts.numberFormat(pcnt, 1) + '%';
                return rtn;
            }
        },
        plotOptions: {
            column: {
                colorByPoint: true,
            }
        },
        colors: [
            '#6994c7',
            '#c86967',
            '#a9c471',
            '#927aaf',
            '#64b6cc',
            '#f5a35f',
            '#577aa3',
            '#874746',
            '#72854a',
            '#417a8a',
            '#ba6926',
            '#81a3cc',
            '#ce8280',
            '#b4ca87',
            '#a08db8',
            '#f3ba8a',
            '#c7d7a5',
            '#8dc7d6',
        ],
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
                    var pcnt = (this.y / this.series.data.map(p => p.y).reduce((a, b) => a + b, 0)) * 100;
                    return Highcharts.numberFormat(pcnt, 1) + '%';
                },
            }
        }]
    });
});
