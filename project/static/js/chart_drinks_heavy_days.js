function chartDrinksHeavyDays(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            height: "350px",
        },
        title: {
            text: chartData.text.title
        },
        subtitle: {
            text: `${chartData.text.threshold_label}: > ${chartData.heavy_threshold.toFixed()} Std Av`
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
                text: chartData.text.unit
            },
            min: 0,
            allowDecimals: false,
            // as on the weekly chart: nothing is shaded for being inside the
            // guideline, and the two bands above it are one hue in two steps
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
                        `${chartData.text.guideline}: ${chartData.low_risk.toFixed(0)}`,
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
                        `${chartData.text.high_risk_guideline}: ${chartData.high_risk.toFixed(0)}`,
                        "var(--drinks-harm)"
                    )
                }
            ]
        },
        tooltip: {
            pointFormat: '{series.name}: <span style="color: {series.color}"><b>{point.y}</b></span><br/>'
        },
        series: [{
            name: chartData.text.heavy,
            data: chartData.data,
            // every bar here is a count of Heavy days, so the whole series is
            // harm — there is no reading on this chart that is not
            color: "var(--drinks-harm)",
            borderWidth: 0,
        }]
    });
};
