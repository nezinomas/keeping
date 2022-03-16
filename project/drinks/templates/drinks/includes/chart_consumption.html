{% load i18n %}
{% load charts %}

<div id="chart_consumption_container"></div>
<script>
    $(function () {
        var categoryLabels = {% months %};

    Highcharts.setOptions({
        lang: {
            thousandsSep: '.',
            decimalPoint: ',',
        }
    });

    Highcharts.chart('chart_consumption_container', {
        chart: {
            height: '350px',
        },
        title: {
            text: ''
        },
        legend: {
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'top',
            floating: true,
            borderWidth: 1,
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
                rotation: -45,
            }
        },
        yAxis: {
            labels: {
            },
            title: {
                text: ''
            },
            plotLines: [{
                color: '#04a41f',
                width: 2,
                value: {{ target|safe }},
                label: {
                    text: '{% translate "Limit" %}: {{ target|floatformat:0|safe }}',
                    align: 'right',
                    x: -5,
                    y: {{ target_label_y|safe }},
                    style: {
                            color: '#04a41f',
                            fontWeight: 'bold'
                        }
                }
            }, {
                color: '#ffc000',
                width: 2,
                value: {{ avg|safe }},
                label: {
                    text: 'Avg: {{ avg|floatformat:0|safe }}',
                    align: 'right',
                    x: -5,
                    y: {{ avg_label_y|safe }},
                    style: {
                        color: '#ffc000',
                        fontWeight: 'bold'
                    }
                }
            }],
            labels: {
                style: {
                    fontSize: '10px',
                    fontFamily: 'Calibri, Verdana',
                }
            }
        },
        tooltip: {
            shared: true,
            pointFormat: '<b>{point.y:,.1f} ml</b><br/>'
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            area: {
                fillOpacity: 0.4
            }
        },
        series: [{
            type: 'area',
            name: '{% translate "Alcohol consumption per day, ml" %}',
            showInLegend: false,
            data: {{ data|safe }},
            color: '#c0504d',
                dataLabels: {
                enabled: true,
                color: '#000',
                align: 'left',
                format: '{point.y:.0f}',
                style: {
                    fontSize: '9px',
                    fontWeight: 'bold',
                    fontFamily: 'Verdana, sans-serif',
                    textOutline: false
                }
            }
        }]
    });
    });
</script>
