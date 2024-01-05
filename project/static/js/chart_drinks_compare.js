function chartCompare(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            height: '350px',
        },
        title: {
            text: ''
        },
        legend: {
            enabled: true,
            backgroundColor: undefined,
        },
        xAxis: {
            min: 0.4,
            max: 10.8,
            tickmarkPlacement: 'on',
            categories: chartData.categories,
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
            crosshairs: true,
            pointFormat: '<span style="color: {series.color}"><b>{series.name}</b>:</span> {point.y:,.0f}ml<br>',
        },
        plotOptions: {
            area: {
                fillOpacity: 0.4
            }
        },
        series: chartData.serries
    });
};
