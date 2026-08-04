function chartTrend(idData, idContainer) {
    const chartData = JSON.parse(document.getElementById(idData).textContent);

    // the raw day is noise the averages are read out of, not a reading of its
    // own, so it is drawn in hairline rather than in a colour
    const dailyColor = "var(--skin-hair)";

    const plotLines = (chartData.target !== null) ? [
    {
        color: "var(--skin-harm)",
        width: 1.5,
        dashStyle: "Dash",
        value: chartData.target,
        zIndex: 10,
        label: paperRuleLabel(
            `${chartData.text.limit}: ${chartData.target.toFixed(chartData.decimals)}`,
            "var(--skin-harm)"
        )
    }] : [];

    Highcharts.chart(idContainer, {
        chart: {
            height: "350px",
            // the raw day runs an order of magnitude above the averages, so
            // aligning ticks across the two axes stretches the averages' axis to
            // the raw day's tick count and leaves them squashed at the bottom
            alignTicks: false,
        },
        title: {
            text: chartData.text.title
        },
        legend: {
            enabled: true,
        },
        xAxis: {
            categories: chartData.categories,
            type: "category",
            tickInterval: Math.ceil(chartData.categories.length / 12),
            labels: {
                rotation: -45,
                formatter: function () {
                    // categories are full ISO dates; show only MM-DD on the axis
                    return this.value.slice(5);
                }
            }
        },
        // the raw day peaks around 9x the 30-day mean, so the two share an x-axis
        // but not a y: the averages keep their own scale and stay readable against
        // the Limit. Both carry the SAME unit, so relative heights across the two
        // axes mean nothing — the shared tooltip is what carries comparable numbers.
        yAxis: [{
            // left stays in default ink: it carries both rolling averages, in
            // two different colours, so tinting it after either one would claim
            // the scale for that series alone
            title: {
                text: chartData.text.unit
            },
            min: 0,
            // the axis holds both averages, so it reaches the 7-day's peak — and
            // the Limit however low they run, since they are read against it
            softMax: (chartData.target !== null) ? chartData.target : undefined,
            // the axis ends just above the 7-day's peak instead of on the next
            // whole tick: at this range a tick is 200, so rounding up to one
            // spends a seventh of the height on empty sky. The top gridline sits
            // below the peak — the ticks are dense enough to read it against
            endOnTick: false,
            maxPadding: 0.02,
            tickPixelInterval: 35,
            plotLines: plotLines,
        },
        {
            // the right axis carries the raw day alone, which is hairline — too
            // pale for an axis — so it keeps the skin's ink labels
            title: {
                text: `${chartData.text.daily}, ${chartData.text.unit}`,
            },
            min: 0,
            // keeps its default top padding so the peak day is not a column
            // flush against the frame, but not the rounding up on top of it
            endOnTick: false,
            opposite: true,
            gridLineWidth: 0,
        }],
        tooltip: {
            shared: true,
            // the 30-day average is what this chart is about, so the border is
            // its colour rather than whichever of the three was hovered — the
            // raw day is drawn in hairline, and a hairline border is no border
            borderColor: "var(--skin-data)",
            // unit and precision come from the payload: the drink-type dropdown
            // decides both, so this must never hardcode ml
            pointFormat: `<span style='color: {series.color}'>{series.name}: <b>{point.y:,.${chartData.decimals}f} ${chartData.text.unit}</b></span><br/>`
        },
        series: [{
            // the raw day as columns, so noise never reads as trend even before
            // colour; at ~365 points each lands near 2px, which reads as texture
            type: "column",
            name: chartData.text.daily,
            data: chartData.daily,
            yAxis: 1,
            color: dailyColor,
            opacity: 1,
            legendIndex: 2,
            borderWidth: 0,
            groupPadding: 0.05,
            pointPadding: 0,
            crisp: false,
            // hairline is right for a column and wrong for a figure, so this row
            // of the shared tooltip reads in ink instead of in the series colour
            tooltip: {
                pointFormat: `<span style='color: var(--skin-ink-muted)'>{series.name}: <b>{point.y:,.${chartData.decimals}f} ${chartData.text.unit}</b></span><br/>`
            }
        },
        {
            // the two averages are one metric over two windows, so they are two
            // steps of one hue: the 30-day is the reading, the 7-day is how it
            // got there
            type: "spline",
            name: chartData.text.r30,
            data: chartData.rolling_30,
            color: "var(--skin-data)",
            legendIndex: 0,
            lineWidth: 2.5,
            marker: {
                enabled: false
            }
        },
        {
            type: "spline",
            name: chartData.text.r7,
            data: chartData.rolling_7,
            color: "var(--skin-data-soft)",
            legendIndex: 1,
            lineWidth: 1.5,
            marker: {
                enabled: false
            }
        }]
    });
};
