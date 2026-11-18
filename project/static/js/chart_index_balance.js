function drawIndexBalance() {
    const chartData = JSON.parse(document.getElementById("chart-balance-data").textContent);
    const euros = (cents) => cents.map((value) => value / 100);

    Highcharts.chart("chart-balance-container", {
        chart: {
            // the tilted months and the legend under them; the expenses chart
            // beside it keeps the same, so both axes sit on one line
            marginBottom: 100,
            events: { render: paperFixEdges },
        },
        legend: {
            enabled: true,
        },
        xAxis: Highcharts.merge(paperCategoryAxis(chartData.categories), {
            labels: { rotation: -45 },
        }),
        yAxis: {
            labels: {
                formatter: paperThousands,
            },
            title: {
                text: "",
            },
        },
        tooltip: {
            split: true,
            pointFormatter() {
                return `${this.series.name}: <b>${paperEuros(this.y)}</b><br>`;
            },
        },
        plotOptions: {
            area: {
                fillOpacity: 0.6,
            },
        },
        series: [{
            type: "area",
            name: chartData.incomes_title,
            data: euros(chartData.incomes),
            color: "var(--skin-gain)",
        }, {
            type: "area",
            name: chartData.expenses_title,
            data: euros(chartData.expenses),
            color: "var(--skin-harm)",
        }],
    });
}
