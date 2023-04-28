function chartReaded(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            type: 'bullet'
        },
        title: {
            text: chartData.chart_title,
            style: {
                fontSize: '16px',
                fontFamily: 'Calibri, Verdana',
            },
        },
        xAxis: {
            lineColor: '#000',
            lineWidth: 2,
            categories: chartData.categories,
            labels: {
                useHTML: true,
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
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
                    fontFamily: 'Calibri, Verdana',
                }
            }
        },
        legend: {
            enabled: false
        },
        tooltip: {
            enabled: false,
        },
        plotOptions: {
            series: {
                enableMouseTracking: false,
                targetOptions: {
                    borderWidth: 0,
                    height:2,
                    color: 'green',
                    width: '110%'
                }
            },
        },
        series: [{
            data: chartData.data,
            color: `rgba(${chartData.chart_column_color}, 0.65)`,
            borderColor: `rgba(${chartData.chart_column_color}, 1)`,
            borderRadius: 0,
            dataLabels: [{
                enabled: true,
                color: `rgba(${chartData.chart_column_color}, 1)`,
                style: {
                    fontSize: '7px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false
                }
            }]
        }, {
            type: 'column',
            borderWidth: 0,
            data: chartData.targets,
            color: 'rgba(0,0,0,0)',
            dataLabels: [{
                enabled: true,
                color: 'green',
                align: 'left',
                x: -23,
                y: -11.5,
                verticalAlign: 'top',
                style: {
                    fontSize: '7px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false
                }
            }]
        }]
    });
};
