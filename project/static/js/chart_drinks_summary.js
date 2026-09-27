function chart_drinks_summary(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);
    const paper = paperTwoPanes();
    const blue = "var(--skin-data)";

    Highcharts.chart(idContainer, Highcharts.merge(paper.base, {
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
                color: blue,
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
                    style: paper.readingDataLabelStyle,
                    formatter: function () {
                        return this.y > 0
                            ? Highcharts.numberFormat(this.y, chartData.decimals)
                            : "";
                    },
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
                    pointFormat: `${chartData.text.per_year}: <span style="color: {series.color}"><b>{point.y:.1f} L</b></span><br>`,
                },
            }),
            // the running year's straight-line pace: a hollow bar behind the filled one
            Highcharts.merge(paper.bottomBars, {
                name: chartData.text.forecast,
                data: chartData.forecast,
                color: "transparent",
                borderColor: blue,
                borderWidth: 1,
                states: { hover: { color: "transparent" } },
                dataLabels: { enabled: false },
                tooltip: {
                    pointFormat: `${chartData.text.forecast}: <span style="color: ${blue}"><b>{point.y:.1f} L</b></span><br>`,
                },
            }),
        ],
    }));
};
