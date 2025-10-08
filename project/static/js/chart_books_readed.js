function chartReaded(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            type: "bullet"
        },
        title: {
            text: chartData.chart_title,
        },
        xAxis: {
            categories: chartData.categories,
            gridLineWidth: 0,
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        plotOptions: {
            series: {
                enableMouseTracking: false,
                targetOptions: {
                    borderWidth: 0,
                    height: 2,
                    color: "#000",
                    width: "110%"
                }
            },
        },
        series: [{
            data: chartData.data,
            color: "var(--chart-alpha-25)",
            borderColor: "var(--secondary)",
            borderRadius: 0,
            borderWidth: 0.5,
            dataLabels: [{
                enabled: true,
                color: "var(--secondary)",
                style: {
                    fontSize: "11px",
                    fontWeight: "bold",
                    textOutline: false
                }
            }]
        }, {
            type: "column",
            borderWidth: 0,
            data: chartData.targets,
            color: "rgba(0,0,0,0)",
            dataLabels: [{
                enabled: true,
                color: "#000",
                align: "left",
                x: -28,
                y: -13,
                verticalAlign: "top",
                style: {
                    fontSize: "11px",
                    fontWeight: "bold",
                    textOutline: false
                }
            }]
        }]
    });
};
