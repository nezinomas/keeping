function chartQuantity(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    Highcharts.chart(idContainer, {
        chart: {
            type: "column",
            height: "350px",
        },
        title: {
            text: ""
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            gridLineWidth: 0,
            crosshair: true,
            labels: {
                rotation: -45,
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
            name: chartData.text.quantity,
            color: `var(--primary-alpha-25)`,
            borderColor: `var(--primary)`,
            borderRadius: 0,
            borderWidth: 0.5,
            data: chartData.data,
            pointPadding: 0,
            pointPlacement: 0,
            dataLabels: {
                enabled: true,
                rotation: 0,
                color: "#000",
                format: "{point.y:.1f}",
            }
        }]
    });
};
