function chartExpenses(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    // convert data
    for(i = 0; i < chartData.data.length; i++) {
        for(y = 0; y < chartData.data[i]['data'].length; y++) {
            chartData.data[i]['data'][y] /= 100
        }
    }

    Highcharts.setOptions({ lang: { decimalPoint: ',', thousandsSep: '.' } });

    Highcharts.chart(idContainer, {
        chart: {
            type: 'column',
            zoomType: 'x',
            panning: {
                enabled: true,
                type: 'x'
            },
            panKey: 'shift'
        },
        title: {
            text: ''
        },

        xAxis: {
            categories: chartData.categories,
            crosshair: true,
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
        },
        yAxis: {
            title: {
                text: ''
            },
            labels: {
                formatter: function () {
                    if (this.value > 500) return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    return Highcharts.numberFormat(this.value, 0);
                },
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                }
            }
        },
        tooltip: {
            headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
            pointFormat:
                '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
                '<td style="padding:0"><b>{point.y:,.1f}€</b></td></tr>',
            footerFormat: '</table>',
            shared: true,
            useHTML: true
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0
            }
        },
        series: chartData.data,
    });
};
