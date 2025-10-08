Highcharts.theme = {
    colors: [
        "var(--chart-tint-0)",
        "var(--chart-tint-10)",
        "var(--chart-tint-20)",
        "var(--chart-tint-30)",
        "var(--chart-tint-40)",
        "var(--chart-tint-50)",
        "var(--chart-tint-55)",
        "var(--chart-tint-60)",
        "var(--chart-tint-65)",
        "var(--chart-tint-70)",
        "var(--chart-tint-75)",
        "var(--chart-tint-80)",
        "var(--chart-tint-85)",
        "var(--chart-tint-90)",
        "var(--chart-tint-90)",
        "var(--chart-tint-90)",
        "var(--chart-tint-90)",
        "var(--chart-tint-90)",
        "var(--chart-tint-90)",
        "var(--chart-tint-90)",
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