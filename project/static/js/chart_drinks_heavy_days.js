function chartDrinksHeavyDays(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // a month up to the Low-risk guideline has not crossed it, so it takes the
    // soft step; only a month over it wears full harm
    const data = chartData.data.map((y) => ({
        y: y,
        color: y > chartData.low_risk ? "var(--skin-harm)" : "var(--skin-harm-soft)",
    }));

    Highcharts.chart(idContainer, {
        chart: Highcharts.merge(PAPER_PANE_TITLE_SPACE, {
            type: "column",
        }),
        legend: {
            enabled: false,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
        },
        yAxis: {
            title: Highcharts.merge(PAPER_PANE_TITLE, {
                text: chartData.text.definition,
            }),
            min: 0,
            allowDecimals: false,
            plotLines: [
                {
                    color: "var(--skin-harm-soft)",
                    width: 1.5,
                    dashStyle: "Dash",
                    value: chartData.low_risk,
                    zIndex: 5,
                    // the soft harm step is a mark colour and fails AA as text
                    label: paperRuleLabel(
                        `${chartData.text.guideline}: ${chartData.low_risk.toFixed(0)}`,
                        "var(--skin-ink-muted)"
                    )
                },
                {
                    color: "var(--skin-harm)",
                    width: 1.5,
                    dashStyle: "Dash",
                    value: chartData.high_risk,
                    zIndex: 5,
                    label: paperRuleLabel(
                        `${chartData.text.high_risk_guideline}: ${chartData.high_risk.toFixed(0)}`,
                        "var(--skin-harm)"
                    )
                }
            ]
        },
        tooltip: {
            // in ink: the soft harm step fails AA as text
            pointFormat: '{series.name}: <b>{point.y}</b><br/>'
        },
        series: [{
            name: chartData.text.heavy,
            data: data,
            color: "var(--skin-harm)",
            borderWidth: 0,
        }]
    });
};
