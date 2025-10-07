function annotationLabels(arrTotal, arrProfit, arrInvested) {
    let total = new Array(arrTotal.length)

    for(i = 0; i < arrTotal.length; i++) {
        let y_val = arrTotal[i];
        if (arrProfit[i] < 0) {
            y_val = arrInvested[i]
        }
        total[i] = {
            point: {
                xAxis: 0,
                yAxis: 0,
                x: i,
                y: y_val
            }
        }
    }
    return total;
};

function chartSavings(container) {
    const positive_text = "var(--positive-text)";
    const negative_text = "var(--negative-text)";
    const chartData = JSON.parse(document.getElementById(`${container}_data`).textContent);

    // convert data
    for (i = 0; i < chartData.categories.length; i++) {
        chartData.invested[i] /= 100;
        chartData.profit[i] /= 100;
        chartData.total[i] /= 100;
    }

    Highcharts.chart(container, {
        chart: {
            type: "column",
            spacingRight: 25,
        },
        title: {
            text: chartData.title,
        },
        subtitle: {
            text: ""
        },
        annotations: [{
            draggable: "",
            labelOptions: {
                useHTML: true,
                crop: false,
                overflow: "none",
                y: -8,
                style: {
                    fontSize: "11px",
                    fontFamily: "Helvetica, sans-serif",
                },
                formatter:function(){
                    let i = this.x
                    let y = chartData.total[i];
                    return `${Highcharts.numberFormat(y, 0)}`
                }
            },
            labels: annotationLabels(chartData.total, chartData.profit, chartData.invested),
        }],
        xAxis: {
            categories: chartData.categories,
            crosshair: true,
            gridLineWidth: 0,
        },
        yAxis: {
            title: {
                text: ""
            },
            labels: {
                enabled: true,
                formatter: function () {
                    if (this.value >= 100 || this.value <= 100) {
                        return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    }
                    return Highcharts.numberFormat(this.value, 0);
                },
            },
            plotLines: [{
                color: "#c0c0c0",
                width: 1,
                value: 0,
                zIndex:2
            }],
            stackLabels: {
                enabled: false,
            },
            startOnTick: false,
        },
        tooltip: {
            pointFormat: "{point.y:,.0f}",
            formatter: function () {
                return `
                    <div><b>${chartData.categories[this.x]}</b></div>
                    <div class="">${chartData.text_profit}: ${chartData.proc[this.point.x]}%</div>
                `
            }
        },
        plotOptions: {
            column: {
                stacking: "normal",
                opacity: 0.9,
            },
        },
        series: [{
            name: chartData.text_profit,
            data: chartData.profit,
            color: "var(--chart-positive-dark)",
            opacity: 0.8,
            borderColor: "var(--chart-positive-super-dark)",
            borderWidth: 0.5,
            borderRadius: 0,
            dataLabels: {
                useHTML: true,
                enabled: true,
                formatter: function () {
                    let val = Highcharts.numberFormat(this.y, 0)
                    if (val == 0) {
                        return "";
                    } else {
                        let color = (val < 0) ? negative_text : positive_text;
                        return `<div class="text-center" style="width: ${this.point.pointWidth}px;"><span style="color:${color};">${val}</span></div>`;
                    }
                },
            }
        }, {
            name: chartData.text_invested,
            data: chartData.invested,
            color: "var(--chart-warning)",
            borderColor: "var(--chart-warning-super-dark)",
            borderWidth: 0.5,
            borderRadius: 0,
            dataLabels: {
                useHTML: true,
                enabled: true,
                verticalAlign: "top",
                formatter: function () {
                    return `<div class="text-center" style="width: ${this.point.pointWidth}px;">${Highcharts.numberFormat(this.y, 0)}</div>`;
                },
                style: {
                    color: "var(--warning-text)"
                },
            }
        }]
    }, function (chartObj) {
        // paint in red negative profit
        let series = chartObj.series[0];
        series.data.forEach((point, i) => {
            if (point.negative) {
                point.color = negative_text; /* + tooltip border color */
                point.graphic.css({ stroke: "var(--chart-negative-super-dark)", color: "var(--chart-negative-dark)" });
            } else {
                point.update({});
            }
        });
    });
};
