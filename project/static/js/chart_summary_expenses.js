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
            text: '',
        },

        xAxis: {
            categories: chartData.categories,
            crosshair: true,
            lineColor: '#000',
            lineWidth: 2,
            labels: {
                style: {
                    fontSize: '10px',
                },
            },
        },
        yAxis: {
            title: {
                text: ''
            },
            labels: {
                formatter: function () {
                    if (this.value > 500) {
                        return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    }
                    return Highcharts.numberFormat(this.value, 0);
                },
                style: {
                    fontSize: '10px',
                }
            }
        },
        tooltip: {
            style: {
                fontSize: '12px',
            },
            headerFormat: '<div class="mb-2">{point.key}</div>',
            pointFormat:
                '<div class="mb-2"><span style="color:{series.color};">{series.name}:</span> ' +
                '<span> <b>{point.y:,.1f}€</b></span></div>',
            footerFormat: '',
            shared: true,
            useHTML: true,
            backgroundColor: '#FFF',
            borderWidth: 1,
            shadow: true,
            opacity: 1,
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0,
                borderRadius: 0,
            }
        },
        series: chartData.data,
    });
};
