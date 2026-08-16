// One category axis and one count, which is every reading Counts draws.
// `chart_paper.js` supplies the ground, the faces, the axes and the gridlines.
function chartPeriodicity(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

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
            text: chartData.chart_title,
        },
        subtitle: {
            text: chartData.subtitle,
        },
        legend: {
            enabled: false,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
        },
        yAxis: {
            title: {
                text: ""
            },
            min: 0,
            allowDecimals: false,
        },
        tooltip: {
            headerFormat: "",
            pointFormat: "{point.category}: <b>{point.y:.0f}</b><br>",
        },
        series: [{
            data: chartData.data,
            color: "var(--skin-data-tint)",
            borderColor: "var(--skin-data)",
            borderWidth: 0.5,
            dataLabels: {
                enabled: true,
                // an empty category has no bar to hang a figure on
                formatter: function () {
                    return this.y != 0 ? this.y : "";
                },
            }
        }]
    });
};
