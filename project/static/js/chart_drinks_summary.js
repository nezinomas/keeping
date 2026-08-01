function chart_drinks_summary(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            // an explicit bottom margin wins over Highcharts' own layout, so
            // everything below the plot has to fit inside it: the year labels,
            // the per-year data labels that sit 25px *under* their points, and
            // — since the legend moved down there — the legend too. It was 67,
            // which was enough for the first two and left the legend sitting on
            // top of the years
            marginBottom: 100,
        },
        title: {
            text: chartData.text.title,
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            min: 0.49,
            max: chartData.categories.length - 1.49,
            categories: chartData.categories,
            type: "category",
            tickmarkPlacement: "on",
        },
        yAxis: [{
            labels: {
                format: "{value:.0f}",
                style: {
                    color: "var(--chart-negative)",
                },
            },
            title: {
                text: "",
                style: {
                    color: "var(--chart-negative)",
                }
            },
        }, {
            opposite: true,
            labels: {
                format: "{value:.0f}",
                style: {
                    color: "var(--chart-negative-super-dark)",
                },
            },
            title: {
                text: "",
                style: {
                    color: "var(--chart-negative-super-dark)",
                }
            },
        }],
        tooltip: {
            pointFormat: `<b>{point.y:,.${chartData.decimals}f} ${chartData.unit}</b><br>`,
        },
        series: [{
            name: chartData.text.per_day,
            yAxis: 0,
            data: chartData.data_ml,
            color: "var(--chart-negative)",
            type: "area",
            marker: {
                fillColor: '#FFFFFF',
                lineWidth: 2,
                lineColor: null // inherit from series
            },
            dataLabels: {
                enabled: true,
                // Std Av needs its decimal; rounding it to whole numbers would
                // flatten a year of 1.0 a day onto the same label as 1.4
                format: `{point.y:.${chartData.decimals}f}`,
                y: -25,
                verticalAlign:"top",
                color: "var(--chart-negative-super-dark)",
                style: {
                    textOutline: 0,
                },
            },
            enableMouseTracking: false,
            fillOpacity: 0.65,
        }, {
            name: chartData.text.per_year,
            yAxis: 1,
            data: chartData.data_alcohol,
            color: "var(--chart-negative-super-dark)",
            type: "line",
            dataLabels: {
                enabled: true,
                format: "{point.y:.1f}",
                y: 25,
                color: "var(--chart-negative-super-dark)",
                style: {
                    textOutline: 0,
                },
            },
            enableMouseTracking: false,
        }],
    });
};
