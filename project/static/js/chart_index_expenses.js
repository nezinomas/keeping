// the palest bar's share of the data hue; the biggest bar takes all of it
var INDEX_EXPENSES_PALEST = 20;

function drawIndexExpenses() {
    const chartData = JSON.parse(document.getElementById("chart-expenses-data").textContent);
    const total = chartData.reduce((sum, type) => sum + type.y, 0) / 100;
    // a type's part of the year's expenses; a type that spent nothing prints none
    const percentOfYear = (y) => (y ? Highcharts.numberFormat(y / total * 100, 1) + "%" : "");
    // the types come biggest first: each bar a step paler than the one before
    const step = (100 - INDEX_EXPENSES_PALEST) / Math.max(chartData.length - 1, 1);
    const types = chartData.map((type, i) => ({
        name: type.name,
        y: type.y / 100,
        color: `color-mix(in srgb, var(--skin-data) ${100 - i * step}%, transparent)`,
    }));

    Highcharts.chart("chart-expenses-container", {
        chart: {
            type: "column",
            // the balance chart's beside it, so both axes sit on one line
            marginBottom: 100,
        },
        xAxis: {
            type: "category",
            crosshair: true,
            labels: {
                rotation: -45,
            },
        },
        yAxis: {
            title: {
                text: "",
            },
            labels: {
                formatter: paperThousands,
            },
        },
        tooltip: {
            shared: true,
            formatter: function () {
                const point = this.points[0];
                return `
                    <b>${point.key}</b><br>
                    ${paperEuros(point.y)}<br>
                    ${percentOfYear(point.y)}
                `;
            },
        },
        series: [{
            data: types,
            dataLabels: {
                useHTML: true,
                enabled: true,
                rotation: -90,
                align: "center",
                crop: false,
                overflow: "allow",
                y: 2,
                formatter: function () {
                    return percentOfYear(this.y);
                },
            },
        }],
    });
}
