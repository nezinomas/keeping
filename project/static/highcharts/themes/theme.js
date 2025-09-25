Highcharts.theme = {
    colors: [
        "var(--chart-color-0)",
        "var(--chart-color-1)",
        "var(--chart-color-2)",
        "var(--chart-color-3)",
        "var(--chart-color-4)",
        "var(--chart-color-5)",
        "var(--chart-color-6)",
        "var(--chart-color-7)",
        "var(--chart-color-8)",
        "var(--chart-color-9)",
        "var(--chart-color-10)",
    ],
    chart: {
        backgroundColor: null,
        style: {
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
    tooltip: {
        borderWidth: 0,
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
        title: {
            style: {
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
        itemStyle: {
            fontWeight: "bold",
            fontSize: "13px",
        },
    },
    credits: {
        enabled: false,
    },
    tooltip: {
        shadow: true,
        useHTML: true,
        backgroundColor: "#FFF",
        borderWidth: 1,
        outside : true,
        style: {
            fontSize: "12px",
        },
    },
    plotOptions:{
        candlestick: {
            lineColor: "#404048"
        },
        series: {
            dataLabels: {
                style: {
                    fontSize: "11px",
                    fontWeight: "bold",
                    textOutline: false,
                },
            }
        }
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