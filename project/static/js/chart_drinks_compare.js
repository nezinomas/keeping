function chartCompare(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });
    Highcharts.chart(idContainer, {
        chart: {
            height: '350px',
        },
        title: {
            text: ''
        },
        legend: {
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 1,
        },
        xAxis: {
            min: 0.4,
            max: 10.8,
            lineColor: '#000',
            lineWidth: 2,
            gridLineWidth: 1,
            tickmarkPlacement: 'on',
            categories: chartData.categories,
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
                rotation: -45,
            }
        },
        yAxis: {
            labels: {
            },
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
        tooltip: {
            shared: true,
            crosshairs: true,
            pointFormat: '<span style="color: {series.color}"><b>{series.name}</b>:</span> {point.y:,.0f}ml<br>',
            style: {
                fontSize: '13px',
                fontFamily: 'Calibri, Verdana',
            },
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            area: {
                fillOpacity: 0.4
            }
        },
        series: chartData.serries
    });
};