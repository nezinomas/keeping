function chartQuantity(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            type: 'column',
            height: '350px',
        },
        title: {
            text: ''
        },
        xAxis: {
            categories: chartData.categories,
            type: 'category',
            gridLineWidth: 0,
            crosshair: true,
            labels: {
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
            pointFormat: '{series.name}: <b>{point.y:.1f}</b><br/>',
        },
        plotOptions: {
            bar: {
                grouping: false,
                shadow: false,
                pointWidth: 13,
            }
        },
        series: [{
            name: chartData.text.quantity,
            color: 'rgba(70, 171, 157,0.65)',
            borderColor: 'rgba(70, 171, 157, 1)',
            data: chartData.data,
            pointPadding: 0,
            pointPlacement: 0,
            borderRadius: 0,
            dataLabels: {
                enabled: true,
                rotation: 0,
                color: '#000',
                format: '{point.y:.1f}',
                style: {
                    fontSize: '12px',
                    fontFamily: 'Calibri, sans-serif',
                    textOutline: false
                }
            }
        }]
    });
};
