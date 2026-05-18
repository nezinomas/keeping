document.addEventListener('DOMContentLoaded', () => {
    const chartData = JSON.parse(document.getElementById("chart-balance-data").textContent);
    // convert data
    for(i = 0; i < 12; i++) {
        chartData.incomes[i] /= 100
        chartData.expenses[i] /= 100
    }

    Highcharts.chart("chart-balance-container", {
        chart: {
            type: "column",
            marginBottom: 74,
        },
        title: {
            text: "",
        },
        legend: {
            enabled: true,
            backgroundColor: undefined,
            itemStyle: {
                fontWeight: "normal",
                fontSize: "11px",
                color: "#6c757d"
            }
        },
        xAxis: {
            categories: chartData.categories,
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
                },
                formatter: function () {
                    const monthsLt = ["Sausis", "Vasaris", "Kovas", "Balandis", "Gegužė", "Birželis", "Liepa", "Rugpjūtis", "Rugsėjis", "Spalis", "Lapkritis", "Gruodis"];
                    const num = parseInt(this.value, 10);
                    if (!isNaN(num) && num >= 1 && num <= 12) {
                        return monthsLt[num - 1];
                    }
                    return this.value;
                }
            },
        },
        yAxis: {
            gridLineColor: "rgba(0, 0, 0, 0.04)",
            labels: {
                style: {
                    fontSize: "10px",
                    color: "#6c757d"
                },
                formatter: function () {
                    if (this.value >= 100) {
                        return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    }
                    return Highcharts.numberFormat(this.value, 0);
                },
            },
            title: {
                text: ""
            },
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
                const monthsLt = ["Sausis", "Vasaris", "Kovas", "Balandis", "Gegužė", "Birželis", "Liepa", "Rugpjūtis", "Rugsėjis", "Spalis", "Lapkritis", "Gruodis"];
                const num = parseInt(this.x, 10);
                const monthName = (!isNaN(num) && num >= 1 && num <= 12) ? monthsLt[num - 1] : this.x;
                
                let html = `<div style="padding: 4px; min-width: 150px;">`;
                html += `<div style="font-weight: 600; font-size: 13px; color: #1e293b; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">${monthName}</div>`;
                this.points.forEach(point => {
                    html += `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 12px;">
                            <span style="display: flex; align-items: center; gap: 6px;">
                                <span style="color:${point.series.color}; font-size: 14px; line-height: 1;">●</span>
                                <span style="color: #64748b; font-weight: 500;">${point.series.name}</span>
                            </span>
                            <span style="font-weight: 600; color: #0f172a;">${Highcharts.numberFormat(point.y, 0)} €</span>
                        </div>
                    `;
                });
                html += `</div>`;
                return html;
            }
        },
        plotOptions: {
            column: {
                grouping: false,
                borderWidth: 0,
                borderRadius: 2,
            }
        },
        series: [{
            name: chartData.incomes_title,
            data: chartData.incomes,
            color: "rgba(6, 145, 255, 0.45)",
            pointPadding: 0.25
        }, {
            name: chartData.expenses_title,
            data: chartData.expenses,
            color: "rgba(220, 96, 108, 1.0)",
            pointPadding: 0.35
        }]
    });
});
