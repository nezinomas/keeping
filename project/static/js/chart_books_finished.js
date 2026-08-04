// Finished by year, drawn against each year's Goal.
//
// `chart_paper.js` supplies the ground, the faces, the axes, the gridlines and
// the data labels, so what is left here is the bullet's own shape: the bar, the
// rule it is measured against, and the two figures naming them.
function chartFinished(idData, idContainer) {
    const chartData = JSON.parse(
        document.getElementById(idData).textContent
    );

    Highcharts.chart(idContainer, {
        chart: {
            type: "bullet"
        },
        title: {
            text: chartData.chart_title,
        },
        xAxis: {
            categories: chartData.categories,
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        plotOptions: {
            series: {
                enableMouseTracking: false,
                // the Goal, drawn across the bar it measures: ink, because a rule
                // a figure is read against is chrome, and chrome carries no hue
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
            // the year's Finished count, in the data hue — a pale tint drawn
            // inside a solid line of it, square like every other surface in this
            // skin. The Habits profile names this shape "the books chart's" and
            // it is right: a 25% wash inside a solid edge is what this chart drew
            // before the skin reached it, so what changes here is only which
            // palette the wash and the edge come out of. It also keeps the Goal's
            // rule readable where the bar has grown past it — an ink line over a
            // solid block of data hue is the one place this chart could go muddy
            color: "var(--skin-data-tint)",
            borderColor: "var(--skin-data)",
            borderWidth: 0.5,
            borderRadius: 0,
            dataLabels: {
                enabled: true
            }
        }, {
            // a transparent column carrying nothing but the Goal's figure — the
            // rule itself is drawn by the series above, which has no label of its
            // own to hang a number on
            type: "column",
            data: chartData.targets,
            color: "rgba(0,0,0,0)",
            borderWidth: 0,
            dataLabels: {
                enabled: true,
                // muted, though the rule it names is ink: a year that all but met
                // its Goal puts the two figures at the same height, and the count
                // is the reading while the Goal is only what it is read against.
                // The rule itself cannot recede with it — it crosses the bar,
                // where anything short of ink washes out against the data hue
                color: "var(--skin-ink-muted)",
                align: "left",
                x: -28,
                y: -13,
                verticalAlign: "top"
            }
        }]
    });
};
