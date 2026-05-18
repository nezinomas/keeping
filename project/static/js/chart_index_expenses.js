document.addEventListener('DOMContentLoaded', () => {
    const chartData = JSON.parse(document.getElementById("chart-expenses-data").textContent);
    // convert data
    for (var key in chartData) {
        chartData[key]["y"] /= 100;
    }

    Highcharts.chart("chart-expenses-container", {
        chart: {
            type: "column",
            marginBottom: 74,
        },
        title: {
            text: ""
        },
        xAxis: {
            type: "category",
            lineWidth: 0,
            tickWidth: 0,
            gridLineWidth: 0,
            crosshair: false,
            labels: {
                rotation: -45,
                style: {
                    fontSize: "10px",
                    color: "#6c757d"
                }
            }
        },
        yAxis: {
            gridLineColor: "rgba(0, 0, 0, 0.04)",
            title: {
                text: ""
            },
            labels: {
                style: {
                    fontSize: "10px",
                    color: "#6c757d"
                },
                formatter: function () {
                    if (this.value >= 100) { return Highcharts.numberFormat(this.value / 1000, 1) + "k"; }
                    return Highcharts.numberFormat(this.value, 0);
                },
            }
        },
        tooltip: {
            shared: true,
            useHTML: true,
            backgroundColor: "rgba(255, 255, 255, 0.98)",
            borderWidth: 0,
            borderRadius: 8,
            padding: 12,
            shadow: {
                color: "rgba(0, 0, 0, 0.08)",
                offsetX: 0,
                offsetY: 6,
                opacity: 0.12,
                radius: 16
            },
            style: {
                fontFamily: "inherit",
                fontSize: "12px",
                color: "#2b2b2b"
            },
            formatter: function () {
                const point = this.points[0];
                const total = point.series.data.map(p => p.y).reduce((a, b) => a + b, 0);
                const pcnt = (point.y / total) * 100;
                return `
                    <div style="padding: 4px; min-width: 140px;">
                        <div style="font-weight: 600; font-size: 13px; color: #1e293b; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">${point.key}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 12px;">
                            <span style="color: #64748b; font-weight: 500;">Amount:</span>
                            <span style="font-weight: 600; color: #0f172a;">${Highcharts.numberFormat(point.y, 0)} €</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
                            <span style="color: #64748b; font-weight: 500;">Of total:</span>
                            <span style="font-weight: 600; color: #0f172a;">${Highcharts.numberFormat(pcnt, 1)}%</span>
                        </div>
                    </div>
                `;
            }
        },
        plotOptions: {
            column: {
                colorByPoint: true,
                borderWidth: 0,
                borderRadius: 2,
                pointPadding: 0.35,
            }
        },
        series: [{
            data: chartData,
            dataLabels: {
                useHTML: true,
                enabled: true,
                rotation: 0,
                color: "#6c757d",
                align: "center",
                crop: false,
                overflow: "allow",
                y: -12,
                style: {
                    fontSize: "9px",
                    fontWeight: "normal",
                    textOutline: "none"
                },
                formatter: function() {
                    const pcnt = (this.y / this.series.data.map(p => p.y).reduce((a, b) => a + b, 0)) * 100;
                    return Highcharts.numberFormat(pcnt, 1) + "%";
                },
            }
        }]
    });
});
