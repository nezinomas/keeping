// The years take their colours from `chart_drinks_paper.js`: one hue in six
// steps, palest year first, because the years this chart lays side by side are
// ordered. Beyond six the steps repeat, and the legend and tooltip are what
// carry a year's identity.
function chartCompare(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
        },
        title: {
            text: chartData.title || ""
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            min: 0.4,
            max: 10.8,
            tickmarkPlacement: "on",
            categories: chartData.categories,
            labels: {
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
            crosshairs: true,
            pointFormat: `<span style="color: {series.color}"><b>{series.name}</b>:</span> {point.y:,.${chartData.decimals}f} ${chartData.unit}<br>`,
        },
        plotOptions: {
            area: {
                fillOpacity: 0.25
            }
        },
        // the last year in is the newest, so it is the one drawn heaviest
        series: chartData.serries.map(function (series, index) {
            const newest = index === chartData.serries.length - 1;
            return Object.assign({}, series, { lineWidth: newest ? 2.5 : 1.5 });
        })
    });
};
