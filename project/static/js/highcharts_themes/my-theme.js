Highcharts.theme = {
    colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572',
             '#FF9655', '#FFF263', '#6AF9C4'],

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