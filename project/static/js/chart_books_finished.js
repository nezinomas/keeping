// Finished by year, drawn against each year's Goal; `chart_paper.js` supplies the rest.
function chartFinished(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );
    const text = chartData.text;

    Highcharts.chart(idContainer, {
        chart: {
            type: "bullet"
        },
        xAxis: {
            categories: chartData.categories,
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        // a phone prints no Goal figure, so its tooltip names the Goal instead
        tooltip: {
            pointFormatter: function () {
                const goal = this.target > 0
                    ? `<br/>${text.goal}: <b>${this.target}</b>`
                    : "";
                return `${text.finished}: <b>${this.y}</b>${goal}`;
            },
        },
        plotOptions: {
            series: {
                enableMouseTracking: !PAPER_WIDE,
                // a rule a figure is read against is chrome, so the Goal is ink
                targetOptions: {
                    borderWidth: 0,
                    height: 2,
                    color: "var(--skin-ink)",
                    width: "110%"
                }
            },
        },
        series: [{
            data: chartData.data,
            // a wash inside a solid edge keeps the ink Goal readable across the bar
            color: "var(--skin-data-tint)",
            borderColor: "var(--skin-data)",
            borderWidth: 0.5,
            borderRadius: 0,
            dataLabels: {
                enabled: true
            }
        }, {
            // the bullet has no label of its own to hang the Goal's figure on; a
            // phone has no room for the figure, and the column would take the tap
            type: "column",
            data: chartData.targets,
            visible: PAPER_WIDE,
            color: "transparent",
            borderWidth: 0,
            dataLabels: {
                enabled: true,
                align: "left",
                x: -28,
                y: -13,
                verticalAlign: "top"
            }
        }]
    });
};
