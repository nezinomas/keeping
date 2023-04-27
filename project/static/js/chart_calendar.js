function chartCalender (idData, idContainer) {
  const chartData = JSON.parse(
    document.getElementById(idData).textContent
  );

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
            load: function() {
                var series = this.series;
                var bbox;
                series.forEach(function(s) {
                    bbox = s.dataLabelsGroup.getBBox(true);
                    this.renderer.text(
                            s.name,
                            bbox.x + this.plotLeft + bbox.width / 2,
                            bbox.height + 20
                        )
                        .attr({
                            align: 'center'
                        })
                        .css({
                            color: '#666666',
                            fontSize: '11px'
                        })
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
            fontSize: '9px'
          }
        },
    },

    colorAxis: {
        min: 0,
        max: 10,
        stops: [
            [0,   '#ffffff'],	 /* empty cell */
            [0.001, '#f4f4f4'],  /* day without record */
            [0.002, '#dfdfdf'],  /* saturday */
            [0.003, '#c3c4c2'],  /*	sunday */
            [0.005, '#c9edff'],  /*	current day */
            [0.01, '#58a70f'],
            [0.4, '#FFFE55'],
            [0.6, '#F5C142'],
            [0.8, '#DF8244'],
            [1, '#B02418']
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
    	useHTML: true,
      formatter: function () {
        if (this.point.value==0) {
          return false;
        }
        var s = this.point.date;
        if(this.point.value >= 0.1) {
        	s += `<div class="gap">${chartData.text.gap} ${this.point.gap}d.</div>`;
          s += `<div class="qty">${chartData.text.quantity} ${this.point.qty.toFixed(1)}</div>`;
        }
        return s;
      }
    },

    plotOptions: {
      series: {
        /*
        show the week number under the calendar blocks
        use the datas of last block row and move it down
        */
        dataLabels: {
          enabled: true,
          y: 20,
          crop: false,
          overflow: 'allow',
          formatter: function() {
            if(this.point.y == 6 || this.point.y == 16) {
              return this.point.week;
            }
            else {
              return null;
            }
          },
          style: {
            fontSize: '10px',
            color: '#999999',
            fontWeight: 'normal',
            textOutline: 'none'
          },
        },
        borderColor: '#ffffff',
        borderWidth: 2
      }
    },
    series: chartData.data
  });
};
