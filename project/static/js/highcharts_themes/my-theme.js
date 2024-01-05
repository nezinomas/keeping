Highcharts.theme = {
    xAxis: {
        lineColor: '#000',
        lineWidth: 2,
        labels: {
            style: {
                fontSize: '10px',
            },
        }
    },
    yAxis: {
        labels: {
            style: {
                fontSize: '10px',
            }
        },
        minorTicks: false,
    },
    credits: {
        enabled: false
    },
    tooltip: {
        backgroundColor: '#FFF',
        borderWidth: 1,
        shadow: true,
        useHTML: true,
        style: {
            fontSize: '12px',
        },
    },
};

// Apply the theme
Highcharts.setOptions(Highcharts.theme);

// Set decimal point format
Highcharts.setOptions({
    lang: {
        thousandsSep: '.',
        decimalPoint: ',',
    }
});