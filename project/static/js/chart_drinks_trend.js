function chartTrend(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    const plotLines = (chartData.target !== null) ? [
    {
        color: "#333",
        width: 2,
        value: chartData.target,
        zIndex: 10,
        label: {
            text: `${chartData.text.limit}: ${chartData.target.toFixed()}`,
            align: "right",
            x: -5,
            style: {
                color: "#333",
                fontWeight: "bold"
            }
        }
    }] : [];

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
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
                    // categories are full ISO dates; show only MM-DD on the axis
                    return this.value.slice(5);
                }
            }
        },
        // the raw day peaks around 9x the 30-day mean, so the two share an x-axis
        // but not a y: the averages keep their own scale and stay readable against
        // the Limit. Both are ml/day, so relative HEIGHTS across the two axes mean
        // nothing — the shared tooltip is what carries the comparable numbers.
        yAxis: [{
            title: {
                text: chartData.text.unit
            },
            min: 0,
            plotLines: plotLines,
        },
        {
            title: {
                text: `${chartData.text.daily}, ${chartData.text.unit}`
            },
            min: 0,
            opposite: true,
            gridLineWidth: 0,
        }],
        tooltip: {
            shared: true,
            borderColor: '#ccc',
            pointFormat: "<span style='color: {series.color}'>{series.name}: <b>{point.y:,.0f} ml</b></span><br/>"
        },
        series: [{
            // "line", not "spline": the raw day swings 0 -> 4000 -> 0 between
            // neighbours, and a spline through that overshoots into negative ml
            type: "line",
            name: chartData.text.daily,
            data: chartData.daily,
            yAxis: 1,
            color: "var(--chart-color-7)",
            opacity: 0.55,
            legendIndex: 2,
            lineWidth: 1,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.r30,
            data: chartData.rolling_30,
            color: "var(--chart-negative-dark)",
            legendIndex: 0,
            lineWidth: 3,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.r7,
            data: chartData.rolling_7,
            color: "#0691ff",
            opacity: 0.5,
            legendIndex: 1,
            lineWidth: 1,
            marker: {
                enabled: false
            }
        }]
    });
};
