function chartPeriodicity(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            type: 'column',
            height: '300px',
        },
        title: {
            text: chartData.title,
        },
        xAxis: {
            lineColor: '#000',
            lineWidth: 2,
            categories: chartData.categories,
            crosshair: true,
            labels: {
                useHTML: true,
                style: {
                    fontSize: '10px',
                },
                formatter: function () { /* use formatter to break word. */
                    return '<div style="word-wrap: break-word; word-break:break-all; width:40px; text-align: right">' + this.value + '</div>';
                },
                rotation: -45,
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
            pointFormat: '<b>{point.y:.0f}</b>',
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
            }
        },
        series: [{
            data: chartData.data,
            color: `rgba(${chartData.chart_column_color}, 0.65)`,
            borderColor: `rgba(${chartData.chart_column_color}, 1)`,
            borderRadius: 0,
            dataLabels: {
                enabled: true,
                rotation: 0,
                color: `rgba(${chartData.chart_column_color}, 1)`,
                formatter: function () {
                    return (this.y != 0) ? this.y : "";
                },
                style: {
                    fontSize: '11px',
                    fontWeight: 'bold',
                    textOutline: false
                }
            }
        }]
    });
};
