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
            categories: chartData.categories,
            crosshair: true,
            gridLineWidth: 0,
            labels: {
                useHTML: true,
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
        },
        tooltip: {
            shared: true,
            headerFormat: '',
            pointFormat: '<b>{point.y:.0f}</b>',
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
