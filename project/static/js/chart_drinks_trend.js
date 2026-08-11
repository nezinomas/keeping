function chartTrend(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    const dailyColor = "var(--skin-hair)";

    const plotLines = (chartData.target !== null) ? [
    {
        color: "var(--skin-harm)",
        width: 1.5,
        dashStyle: "Dash",
        value: chartData.target,
        zIndex: 10,
        label: paperRuleLabel(
            `${chartData.text.limit}: ${chartData.target.toFixed(chartData.decimals)}`,
            "var(--skin-harm)"
        )
    }] : [];

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
            alignTicks: false,
        },
        title: {
            text: chartData.text.title
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            tickInterval: Math.ceil(chartData.categories.length / 12),
            labels: {
                rotation: -45,
                formatter: function () {
                    return this.value.slice(5);
                }
            }
        },
        yAxis: [{
            title: {
                text: chartData.text.unit
            },
            min: 0,
            softMax: (chartData.target !== null) ? chartData.target : undefined,
            endOnTick: false,
            maxPadding: 0.02,
            tickPixelInterval: 35,
            plotLines: plotLines,
        },
        {
            title: {
                text: `${chartData.text.daily}, ${chartData.text.unit}`,
            },
            min: 0,
            endOnTick: false,
            opposite: true,
            gridLineWidth: 0,
        }],
        tooltip: {
            shared: true,
            borderColor: "var(--skin-data)",
            pointFormat: `<span style='color: {series.color}'>{series.name}: <b>{point.y:,.${chartData.decimals}f} ${chartData.text.unit}</b></span><br/>`
        },
        series: [{
            type: "column",
            name: chartData.text.daily,
            data: chartData.daily,
            yAxis: 1,
            color: dailyColor,
            opacity: 1,
            legendIndex: 2,
            borderWidth: 0,
            groupPadding: 0.05,
            pointPadding: 0,
            crisp: false,
            tooltip: {
                pointFormat: `<span style='color: var(--skin-ink-muted)'>{series.name}: <b>{point.y:,.${chartData.decimals}f} ${chartData.text.unit}</b></span><br/>`
            }
        },
        {
            type: "spline",
            name: chartData.text.r30,
            data: chartData.rolling_30,
            color: "var(--skin-data)",
            legendIndex: 0,
            lineWidth: 2.5,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.r7,
            data: chartData.rolling_7,
            color: "var(--skin-data-soft)",
            legendIndex: 1,
            visible: false,
            lineWidth: 1.5,
            marker: {
                enabled: false
            }
        }]
    });
};
