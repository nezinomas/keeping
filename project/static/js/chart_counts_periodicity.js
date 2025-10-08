function chartPeriodicity(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    // if no data
    if (!chartData.categories.length) {
        chartData.categories = ["0"];
        chartData.data = [0];
    }

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            height: "300px",
        },
        title: {
            text: chartData.title,
        },
        xAxis: {
            categories: chartData.categories,
            crosshair: true,
            gridLineWidth: 0,
            labels: {
                useHTML: true,
                formatter: function () { /* use formatter to break word. */
                    return `<div style="word-wrap: break-word; word-break:break-all; width:40px; text-align: right">${this.value}</div>`;
                },
                rotation: -45,
            }
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        tooltip: {
            shared: true,
            headerFormat: "",
            pointFormat: "{point.category}: <b>{point.y:.0f}</b><br>",
        },
        plotOptions: {
            bar: {
                grouping: false,
                shadow: false,
            }
        },
        series: [{
            data: chartData.data,
            color: `var(--chart-alpha-25)`,
            borderColor: `var(--secondary)`,
            borderRadius: 0,
            borderWidth: 0.5,
            dataLabels: {
                enabled: true,
                rotation: 0,
                color: `#333`,
                formatter: function () {
                    return (this.y != 0) ? this.y : "";
                },
                style: {
                    fontSize: "11px",
                    fontWeight: "bold",
                    textOutline: false
                }
            }
        }]
    });
};
