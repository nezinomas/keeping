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
};
// Apply the theme
Highcharts.setOptions(Highcharts.theme);