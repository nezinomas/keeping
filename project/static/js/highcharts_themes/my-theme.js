Highcharts.theme = {
    colors: [
        "#7cb5ec",
        "#f7a35c",
        "#90ee7e",
        "#7798BF",
        "#aaeeee",
        "#ff0066",
        "#eeaaee",
        "#55BF3B",
        "#DF5353",
        "#7798BF",
        "#aaeeee"
    ],
    chart: {
        backgroundColor: null,
        style:{
            fontFamily: "Dosis, sans-serif"
        },
    },
    title: {
        verticalAlign: "top",
        style: {
            fontSize: "16px",
            fontWeight: "bold",
            textTransform: "uppercase"
        }
    },
    tooltip:{
        borderWidth:0,
        backgroundColor: "rgba(219,219,216,0.8)",
        shadow: !1
    },
    xAxis: {
        lineColor: "#000",
        lineWidth: 2,
        gridLineWidth: 1,
        labels: {
            style: {
                fontSize: "10px",
            },
        }
    },
    yAxis: {
        title:{
            style:{
                textTransform: "uppercase"
            }
        },
        labels: {
            style: {
                fontSize: "10px",
            }
        },
        minorTicks: false,
    },
    legend: {
        enabled: false,
        layout: "horizontal",
        align: "right",
        verticalAlign: "top",
        floating: true,
        borderWidth: 0,
        backgroundColor: "#F0F0EA",
        itemStyle:{
            fontWeight: "bold",
            fontSize: "13px",
        },
    },
    credits: {
        enabled: false,
    },
    tooltip: {
        backgroundColor: "#FFF",
        borderWidth: 1,
        shadow: true,
        useHTML: true,
        style: {
            fontSize: "12px",
        },
    },
    plotOptions:{
        candlestick: {
            lineColor: "#404048"
        },
    },
};

// Apply the theme
Highcharts.setOptions(Highcharts.theme);

// Set decimal point format
Highcharts.setOptions({
    lang: {
        thousandsSep: ".",
        decimalPoint: ",",
    }
});