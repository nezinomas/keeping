// A year narrower than this cannot hold its figures apart; the tooltip still names them.
var SUMMARY_LABEL_ROOM_PX = 30;

function dropCrowdedLabels() {
    const axis = this.xAxis[0];
    if (axis.len / axis.categories.length >= SUMMARY_LABEL_ROOM_PX) {
        return;
    }
    this.series.forEach((s) => s.update({ dataLabels: { enabled: false } }));
}

function chart_drinks_summary(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);
    const paper = paperTwoPanes();
    const dataHue = paper.dataHue;
    // a litre reading, in the colour its series keeps at `colourPath`
    const litres = (name, colourPath) =>
        `${name}: <span style="color: {${colourPath}}"><b>{point.y:.1f} L</b></span><br>`;

    Highcharts.chart(idContainer, Highcharts.merge(paper.base, {
        chart: { events: { load: dropCrowdedLabels } },
        xAxis: paper.xAxis(chartData.categories),
        yAxis: [
            Highcharts.merge(paper.paneTop, {
                title: { text: chartData.text.per_day },
            }),
            Highcharts.merge(paper.paneBottom, {
                title: { text: chartData.text.per_year },
            }),
        ],
        series: [
            {
                type: "area",
                yAxis: 0,
                opacity: 0.85,
                name: chartData.text.per_day,
                showInLegend: false,
                data: chartData.data_ml,
                color: dataHue,
                fillColor: "var(--skin-data-wash)",
                marker: {
                    enabled: true,
                    radius: 2.5,
                    symbol: "circle",
                },
                dataLabels: {
                    enabled: true,
                    verticalAlign: "bottom",
                    y: -8,
                    crop: false,
                    overflow: "allow",
                    formatter: paperFigure(chartData.decimals),
                },
                tooltip: {
                    pointFormat: `${chartData.text.per_day}: <span style="color: {series.color}"><b>{point.y:,.${chartData.decimals}f} ${chartData.unit}</b></span><br>`,
                },
            },
            Highcharts.merge(paper.bottomBars, {
                name: chartData.text.per_year,
                data: chartData.data_alcohol,
                zIndex: 1,
                tooltip: {
                    pointFormat: litres(chartData.text.per_year, "series.color"),
                },
            }),
            // the running year's straight-line pace: a hollow bar behind the filled one
            Highcharts.merge(paper.bottomBars, {
                name: chartData.text.forecast,
                data: chartData.forecast,
                color: "transparent",
                borderColor: dataHue,
                borderWidth: 1,
                states: { hover: { color: "transparent" } },
                dataLabels: { enabled: false },
                tooltip: {
                    pointFormat: litres(chartData.text.forecast, "series.options.borderColor"),
                },
            }),
        ],
    }));
};
