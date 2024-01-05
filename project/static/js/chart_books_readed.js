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
        },
        xAxis: {
            categories: chartData.categories,
            gridLineWidth: 0,
        },
        yAxis: {
            title: {
                text: ''
            },
        },
        plotOptions: {
            series: {
                enableMouseTracking: false,
                targetOptions: {
                    borderWidth: 0,
                    height: 2,
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
                    fontSize: '11px',
                    fontWeight: 'bold',
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
                x: -28,
                y: -13,
                verticalAlign: 'top',
                style: {
                    fontSize: '11px',
                    fontWeight: 'bold',
                    textOutline: false
                }
            }]
        }]
    });
};
