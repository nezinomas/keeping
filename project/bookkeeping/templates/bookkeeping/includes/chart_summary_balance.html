{% load i18n %}

{% translate 'Incomes/Expenses' as chart_title %}

<div id="container-balance-summary"></div>

<script>
    $(function () {
        var categoryLabels = {{ balance_categories }};

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart('container-balance-summary', {
        chart: {
            spacingRight: 25,
        },
        title: {
            text: '{{ chart_title }}',
        },
        legend: {
            layout: 'horizontal',
            align: 'right',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 0,
            x: -10,
        },
        xAxis: {
            min: 0.49,
            max: categoryLabels.length - 1.49,
            categories: categoryLabels,
            type: 'category',
            lineColor: '#000',
            lineWidth: 2,
            gridLineWidth: 1,
            tickmarkPlacement: 'on',
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
        },
        yAxis: {
            labels: {
                formatter: function () {
                    if (this.value >= 100) return Highcharts.numberFormat(this.value / 1000, 1) + "k";
                    return Highcharts.numberFormat(this.value, 0);
                },
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                },
            },
            title: {
                text: ''
            },

        },
        tooltip: {
            split: true,
            pointFormat: '{series.name}: <b>{point.y:,.0f} €</b><br/>',
                style: {
                    fontSize: '13px',
                    fontFamily: 'Calibri, Verdana',
                },
        },
        plotOptions: {
            area: {
                fillOpacity: 0.5
            },
            area: {
                fillOpacity: 0.5,
            }
        },
        series: [
            {'name': '{% translate "Incomes" %}', 'data': {{ balance_income_data|safe }}, color: '#77933c', 'type': 'area'},
            {'name': '{% translate "Expenses" %}', 'data': {{ balance_expense_data|safe }}, color: '#c0504d', 'type': 'area'},
        ]
    });
    });
</script>
