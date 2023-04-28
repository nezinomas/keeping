function chart_drinks_summary(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart(idContainer, {
        chart: {
            marginBottom: 67,
        },
        title: {
            text: chartData.text.title,
        },
        legend: {
            layout: 'horizontal',
            align: 'right',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 0,
            x: -10,
        },
        xAxis: {
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: 'category',
            lineColor: '#000',
            lineWidth: 2,
            gridLineWidth: 1,
            tickmarkPlacement: 'on',
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
        },
        yAxis: [{
            labels: {
                format: '{value:.0f}',
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                    color: '#46ab9d',
                },
            },
            title: {
                text: '',
                style: {
                    color: '#46ab9d',
                }
            },
        }, {
            opposite: true,
            labels: {
                format: '{value:.0f}',
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                    color: '#d13572',
                },
            },
            title: {
                text: '',
                style: {
                    color: '#d13572',
                }
            },
        }],
        tooltip: {
            pointFormat: '<b>{point.y:,.0f} ml</b><br/>',
                style: {
                    fontSize: '13px',
                    fontFamily: 'Calibri, Verdana',
                },
        },
        series: [{
            name: chartData.text.per_day,
            yAxis: 0,
            data: chartData.data_ml,
            color: '#46ab9d',
            type: 'area',
            dataLabels: {
                enabled: true,
                format: '{point.y:.0f}',
                y: -25,
                verticalAlign:'top',
                color: '#28695f',
                style: {
                    textOutline: 0,
                },
            },
            enableMouseTracking: false,
            fillOpacity: 0.65,
        }, {
            name: chartData.text.per_year,
            yAxis: 1,
            data: chartData.data_alcohol,
            color: '#d13572',
            type: 'line',
            dataLabels: {
                enabled: true,
                format: '{point.y:.1f}',
                y: 25,
                color: '#d13572',
                style: {
                    textOutline: 0,
                },
            },
            enableMouseTracking: false,
        }],
    });
};
