// The year's expenses by type, biggest first: one hue, as the order already says the
// rank; each bar ends in its sum and its part of the year.
function drawIndexExpenses() {
    const chartData = JSON.parse(document.getElementById("chart-expenses-data").textContent);
    const total = chartData.reduce((sum, type) => sum + type.y, 0) / 100;
    // a type that spent nothing prints no figure
    const sumAndShare = (y) => (
        y ? `${paperEuros(y)} · ${Highcharts.numberFormat(y / total * 100, 1)}%` : ""
    );

    Highcharts.chart("chart-expenses-container", {
        chart: {
            type: "bar",
            marginBottom: PAPER_PAIR_MARGIN_BOTTOM,
            events: { load: indexRoomForFigures },
        },
        legend: { enabled: false },
        xAxis: {
            type: "category",
            labels: { step: 1, style: { textOverflow: "none", whiteSpace: "nowrap" } },
        },
        yAxis: paperMoneyAxis(),
        tooltip: {
            formatter() {
                return `<b>${this.key}</b><br>${sumAndShare(this.y)}`;
            },
        },
        series: [{
            data: chartData.map((type) => ({ name: type.name, y: type.y / 100 })),
            color: "var(--skin-data-tint)",
            borderColor: "var(--skin-year-0)",
            borderWidth: 1,
            dataLabels: {
                enabled: true,
                crop: false,
                overflow: "allow",
                formatter() { return sumAndShare(this.y); },
            },
        }],
    });
}

// Room past the plot for the widest bar figure, as drawn, so a long sum is not cut.
function indexRoomForFigures() {
    const widths = this.series[0].points.map((point) => (
        point.dataLabel ? point.dataLabel.getBBox().width : 0
    ));
    const gap = 12; // the figure's 5px off its bar, and air past it
    const margin = { chart: { marginRight: Math.ceil(Math.max(0, ...widths)) + gap } };
    // unanimated: an animated update leaves a phone's figures where the first layout
    // put them, past the chart's edge
    this.update(margin, true, false, false);
}
