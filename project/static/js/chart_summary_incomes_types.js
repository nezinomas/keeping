document.addEventListener('DOMContentLoaded', () => {
    const chartData = JSON.parse(document.getElementById("chart-incomes-types-data").textContent);

    // convert data
    for (i = 0; i < chartData.data.length; i++) {
        for (n = 0; n < chartData.data[i].data.length; n++) {
            chartData.data[i].data[n] /= 100
        }
    }

    Highcharts.chart("chart-incomes-types-container", {
        chart: {
            type: "column",
            spacingRight: 25,
        },
        title: {
            text: chartData.chart_title,
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
            gridLineWidth: 0,
            crosshair: true,
        },
        yAxis: {
            min: 0,
            title: {
                text: "%"
            },
        },
        tooltip: {
            pointFormat: '<span style="color:{series.color}">{series.name}</span>:  <b>{point.y:,.0f}€</b> ({point.percentage:.1f}%)<br>',
            shared: true,
        },
        plotOptions: {
            column: {
                stacking: "percent",
                borderRadius: 0,
                borderWidth: 0,
                dataLabels: {
                    useHTML: true,
                    enabled: true,
                    crop: false,
                    overflow: "none",
                    formatter:function(){
                        return `<div class="text-center" style="width: ${this.point.pointWidth}px;">${Highcharts.numberFormat(this.point.percentage, 1)}%</div>`;
                    },
                    style: {
                        fontWeight: "normal",
                        textOutline: "none",
                        fontSize: "11px",
                    }
                }
            }
        },
        series: chartData.data,
    });
});
