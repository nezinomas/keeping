function chartDrinksWeekly(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            height: "350px",
        },
        title: {
            text: chartData.text.title
        },
        legend: {
            enabled: false,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            tickInterval: Math.ceil(chartData.categories.length / 12),
            labels: {
                formatter: function () {
                    // categories are full ISO dates (week-start); show only MM-DD
                    return this.value.slice(5);
                }
            }
        },
        yAxis: {
            title: {
                text: chartData.text.unit
            },
            min: 0,
            // below the guideline is plain paper: a week inside the guideline is
            // not an achievement to shade. The two bands above it are steps of
            // one hue, because they are two degrees of the same thing
            plotBands: [
                { from: chartData.low_risk, to: chartData.high_risk, color: "var(--drinks-harm-wash)" },
                { from: chartData.high_risk, to: Number.MAX_VALUE, color: "var(--drinks-harm-wash)" }
            ],
            plotLines: [
                {
                    color: "var(--drinks-harm-soft)",
                    width: 1.5,
                    dashStyle: "Dash",
                    value: chartData.low_risk,
                    zIndex: 5,
                    label: drinksRuleLabel(
                        `${chartData.text.guideline}: ${chartData.low_risk.toFixed(1)}`,
                        "var(--drinks-harm-soft)"
                    )
                },
                {
                    color: "var(--drinks-harm)",
                    width: 1.5,
                    dashStyle: "Dash",
                    value: chartData.high_risk,
                    zIndex: 5,
                    label: drinksRuleLabel(
                        `${chartData.text.high_risk_guideline}: ${chartData.high_risk.toFixed(1)}`,
                        "var(--drinks-harm)"
                    )
                }
            ]
        },
        tooltip: {
            useHTML: true,
            formatter: function () {
                const end = chartData.week_ends[this.point.index];
                // the bar's own colour, not the series': each week is coloured
                // by the band it lands in, and the tooltip says which
                return `<span class="tooltip-header">${this.point.category} &ndash; ${end}</span><br/>`
                    + `${this.series.name}: <span style="color: ${this.point.color}">`
                    + `<b>${Highcharts.numberFormat(this.y, 1)} Std Av</b></span>`;
            }
        },
        series: [{
            name: chartData.text.weekly,
            // the bar says what the week was, and only a week past the guideline
            // is coloured for it — the rest of the year stays the data hue
            data: chartData.data.map(function (stdav) {
                if (stdav === null) {
                    return null;
                }

                let color = "var(--drinks-data)";
                if (stdav > chartData.high_risk) {
                    color = "var(--drinks-harm)";
                } else if (stdav > chartData.low_risk) {
                    color = "var(--drinks-harm-soft)";
                }

                return { y: stdav, color: color };
            }),
            borderWidth: 0,
        }]
    });
};
