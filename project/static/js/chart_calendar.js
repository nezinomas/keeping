function chartCalender (idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);
    const ratio = chartData.ratio || 2.5;

    Highcharts.chart(idContainer, {
        chart: {
            type: 'heatmap',
            plotBorderWidth: 0,
            height: 200,
            events: {
                /*
                    show the month name (series.name) as label of every block
                    add text element to the BBox - using SVGRenderer
                */
                load: function () {
                    this.series.forEach(function (serie) {
                        let bbox = serie.dataLabelsGroup.getBBox(true);
                        this.renderer.text(
                            serie.name,
                            bbox.x + this.plotLeft + bbox.width / 2,
                            bbox.height + 20
                        )
                        .attr({align: 'center'})
                        .css({color: '#666666', fontSize: '12px'})
                        .add();
                    }, this);
                }
            }
        },
        title: {
            text: '-',
            style: {
                color: 'white',
            }
        },
        xAxis: {
            type: 'category',
            title: null,
            lineWidth: 0,
            gridLineWidth: 0,
            minorGridLineWidth: 0,
            tickWidth: 0,
            opposite: true,
            labels: {
                /*
                don't show the axis label : it's the category id
                see plotOptions -> dataLabels to show the week number
                */
                enabled: false
            }
        },

        yAxis: {
            type: 'category',
            categories: chartData.categories,
            title: null,
            reversed: true,
            lineWidth: 0,
            gridLineWidth: 0,
            minorGridLineWidth: 0,
            minTickInterval: 1,
            labels: {
                style: {
                    fontSize: '10px'
                }
            },
        },

        colorAxis: {
            min: 0,
            max: 10,
            stops: [
                [0,   '#ffffff'],	 /* empty cell */
                [0.00001, '#f4f4f4'],  /* day without record */
                [0.00002, '#dfdfdf'],  /* saturday */
                [0.00003, '#c3c4c2'],  /*	sunday */
                [0.00005, '#c9edff'],  /*	current day */
                [0.25 / ratio, '#58a70f'],
                [1.0 / ratio, '#FFFE55'],
                [1.5 / ratio, '#F5C142'],
                [2.0 / ratio, '#DF8244'],
                [2.5 / ratio, '#B02418']
            ],
            labels: {
                enabled: true
            }
        },

        legend: {
            enabled: false,
            verticalAlign: 'bottom',
            layout: 'horizontal',
            margin: 30,
            y: 40
        },

        credits: {
            enabled: false
        },

        tooltip: {
            style: {
                fontSize: '12px',
            },
            useHTML: true,
            formatter: function () {
                if (this.point.value==0) {
                    return false;
                }

                let text = `<div>${this.point.date}</div>`;
                if(this.point.value >= 0.01) {
                    text += `<div class="gap my-2">${chartData.text.gap} ${this.point.gap}d.</div>`;
                    text += `<div class="qty">${chartData.text.quantity} ${this.point.qty.toFixed(1)}</div>`;
                }
                return text;
            }
        },

        plotOptions: {
            series: {
                /*
                show the week number under the calendar blocks
                use the datas of last block row and move it down
                */
                borderWidth: 2,
                borderColor: '#ffffff',
                dataLabels: {
                    enabled: true,
                    y: 20,
                    crop: false,
                    overflow: 'allow',
                    style: {
                        fontSize: '10px',
                        color: '#999999',
                        fontWeight: 'normal',
                        textOutline: 'none'
                    },
                    formatter: function() {
                        if(this.point.y == 6 || this.point.y == 16) {
                            return this.point.week;
                        }
                        else {
                            return null;
                        }
                    },
                },
            },
        },
        series: chartData.data
    });
};
