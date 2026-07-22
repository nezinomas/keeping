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
                rotation: -45,
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
            plotBands: [
                { from: 0, to: chartData.low_risk, color: "rgba(76, 175, 80, 0.10)" },
                { from: chartData.low_risk, to: chartData.high_risk, color: "rgba(255, 193, 7, 0.12)" },
                { from: chartData.high_risk, to: Number.MAX_VALUE, color: "rgba(244, 67, 54, 0.12)" }
            ],
            plotLines: [
                {
                    color: "#333",
                    width: 2,
                    value: chartData.low_risk,
                    zIndex: 5,
                    label: {
                        text: `${chartData.text.guideline}: ${chartData.low_risk.toFixed(1)}`,
                        align: "right",
                        x: -5,
                        style: {
                            color: "#333",
                            fontWeight: "bold"
                        }
                    }
                },
                {
                    color: "rgba(244, 67, 54, 1)",
                    width: 2,
                    value: chartData.high_risk,
                    zIndex: 5,
                    label: {
                        text: `${chartData.text.high_risk_guideline}: ${chartData.high_risk.toFixed(1)}`,
                        align: "right",
                        x: -5,
                        style: {
                            color: "rgba(244, 67, 54, 1)",
                            fontWeight: "bold"
                        }
                    }
                }
            ]
        },
        tooltip: {
            useHTML: true,
            formatter: function () {
                const end = chartData.week_ends[this.point.index];
                return `<span class="tooltip-header">${this.point.category} &ndash; ${end}</span><br/>`
                    + `${this.series.name}: <b>${Highcharts.numberFormat(this.y, 1)} Std Av</b>`;
            }
        },
        series: [{
            name: chartData.text.weekly,
            data: chartData.data,
            color: "var(--chart-negative-dark)",
            borderWidth: 0,
        }]
    });
};
