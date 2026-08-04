// The years take steps of one hue, palest year first, because the years this
// chart lays side by side are ordered.
//
// Which steps depends on how many years are plotted, which is why they are picked
// here rather than left to the theme's colour list: that list is read from the
// front, so two years would take the two palest steps and be drawn a hair apart.
// Spreading the years the pool holds over the whole ramp instead keeps the oldest
// palest and the newest darkest at every size — and two years, the commonest
// reading, end up as far apart as the hue goes.
const DRINKS_RAMP_STEPS = 6;

function drinksYearColor(index, count) {
    if (count < 2) {
        return `var(--skin-year-${DRINKS_RAMP_STEPS - 1})`;
    }

    const step = Math.round((index * (DRINKS_RAMP_STEPS - 1)) / (count - 1));

    return `var(--skin-year-${step})`;
}

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
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        tooltip: {
            shared: true,
            crosshairs: true,
            pointFormat: `<span style="color: {series.color}"><b>{series.name}</b>: {point.y:,.${chartData.decimals}f} ${chartData.unit}</span><br>`,
        },
        plotOptions: {
            area: {
                fillOpacity: 0.25
            }
        },
        // the last year in is the newest, so it is the darkest and the heaviest
        series: chartData.serries.map(function (series, index) {
            const count = chartData.serries.length;
            const newest = index === count - 1;

            return Object.assign({}, series, {
                color: drinksYearColor(index, count),
                lineWidth: newest ? 2.5 : 1.5,
            });
        })
    });
};
