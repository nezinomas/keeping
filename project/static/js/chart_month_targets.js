loadChart("chart-targets-data", "chart-targets-container");

function loadChart(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // convert targets
    for(i = 0; i < chartData.target.length; i++) {
        chartData.target[i] /= 100;
    }

    // convert data
    for (key in chartData.fact) {
        chartData.fact[key]["y"] /= 100;
        chartData.fact[key]["target"] /= 100;
    }

    Highcharts.chart(idContainer, {
        chart: {
            type: "bar",
            height: 485,
            marginLeft: chartData.max_category_len * 6.55,
        },
        title: {
            text: ""
        },
        xAxis: {
            categories: chartData.categories,
            gridLineWidth: 0,
            labels: {
                style: {
                    fontWeight: "bold",
                },
            }
        },
        yAxis: {
            title: {
                text: ""
            },
        },
        tooltip: {
            shared: true,
            headerFormat: "",
            pointFormat: "{series.name}: <b>{point.y:.1f}</b><br>",
        },
        series: [{
            name: chartData.targetTitle,
            type: "bar",
            color: "rgba(0,0,0,0.07)",
            data: chartData.target,
            pointWidth: 19,
            dataLabels: {
                enabled: true,
                color: "#000",
                x: -2,
                y: -15,
                overflow: "none",
                crop: false,
                format: "{point.y:.0f}",
                style: {
                    fontSize: "9px",
                    fontWeight: "bold",
                    textOutline: false
                }
            }
        }, {
            name: chartData.factTitle,
            type: "bullet",
            data: chartData.fact,
            pointWidth: 13,
            borderRadius: 0,
            targetOptions: {
                borderWidth: 0,
                height: 2,
                color: "#000",
                width: "200%"
            },
            dataLabels: {
                format: "{point.y:.0f}",
                enabled: true,
                color: "#000",
                align: "right",
                y: -1,
                style: {
                    fontWeight: "bold",
                    textOutline: false,
                },
            },
        }
    ]
    }, function (chartObj) {
        /* align datalabels for expenses that exceeds targets */
        $.each(chartObj.series[1].data, function (i, point) {
            let max = chartObj.series[0].data[point.x].y;
            let {y} = point;

            max = parseFloat(max.toFixed(1));
            y = parseFloat(y.toFixed(1));

            if (y <= max) {
                color = "#5D9C59";
            }
            else {
                p = 28;
                if (y < 100) { p = 21; }
                if (y < 10) { p = -2; }
                point.dataLabel.attr({ x: point.dataLabel.x + p });

                color = (y <= max * 1.1) ? "#FEB56A" : "#EB5353";
            }
            point.color = color;
            point.graphic.attr({ fill: color });
        });
    });
};