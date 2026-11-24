// Grafikai's two month charts, both from `month-charts-data`: the month's balance as
// columns beside the expenses chart, incomes and expenses as lines below them.
function drawIndexMonthCharts() {
    const chartData = JSON.parse(document.getElementById("month-charts-data").textContent);
    const incomes = indexEuros(chartData.incomes);
    const expenses = indexEuros(chartData.expenses);
    const months = {
        incomes: incomes,
        expenses: expenses,
        balances: incomes.map((income, x) => (income === null ? null : income - expenses[x])),
    };
    drawIndexMonthBalance(chartData, months);
    drawIndexIncomesExpenses(chartData, months);
}

// Cents to euros; a month not reached stays Highcharts' gap.
function indexEuros(cents) {
    return cents.map((value) => (value === null ? null : value / 100));
}

// A month's name for a tooltip; the current month says it is not over.
function indexMonthName(chartData, x) {
    const month = chartData.categories[x];
    return chartData.current_month[x] ? `${month} (${chartData.so_far})` : month;
}

// A mark's colours, paler in the current month.
function indexMarkColours(chartData, x, colours) {
    if (!chartData.current_month[x]) {
        return colours;
    }
    return Object.fromEntries(
        Object.entries(colours).map(([key, colour]) => [key, paperFaded(colour)]),
    );
}

function drawIndexMonthBalance(chartData, months) {
    const columns = months.balances.map((y, x) => {
        if (y === null) {
            return null;
        }
        // a month that spent more than it earned is harm
        let colours = { color: "var(--skin-data-tint)", borderColor: "var(--skin-year-0)" };
        if (y < 0) {
            colours = { color: "var(--skin-harm-soft)", borderColor: "var(--skin-harm)" };
        }
        return { y: y, ...indexMarkColours(chartData, x, colours) };
    });

    Highcharts.chart("chart-balance-container", {
        chart: {
            type: "column",
            marginBottom: PAPER_PAIR_MARGIN_BOTTOM,
            events: { render: paperFixEdges },
        },
        legend: { enabled: false },
        xAxis: paperCategoryAxis(chartData.categories),
        yAxis: {
            ...paperMoneyAxis(),
            plotLines: [{ value: 0, color: "var(--skin-ink)", width: 1, zIndex: 3 }],
        },
        tooltip: {
            formatter() {
                return `<b>${indexMonthName(chartData, this.point.index)}</b><br>`
                    + `${chartData.balance_title}: <b>${paperEuros(this.y)}</b>`;
            },
        },
        series: [{
            data: columns,
            borderWidth: 1,
            dataLabels: {
                // twelve figures touch on a phone; the tooltip gives each there
                enabled: PAPER_WIDE,
                // a month at nought has no column to carry a figure
                formatter() { return this.y ? paperMoney(this.y) : ""; },
            },
        }],
    });
}

function drawIndexIncomesExpenses(chartData, months) {
    const line = (name, values, colour, symbol) => ({
        type: "line",
        name: name,
        color: colour,
        marker: { symbol: symbol, radius: 3 },
        data: values.map((y, x) => (
            y === null ? null : { y: y, ...indexMarkColours(chartData, x, { color: colour }) }
        )),
    });
    // the months so far, read against their average; a year not begun has no rule
    const average = (cents, colour) => (cents ? [{
        value: cents / 100,
        color: colour,
        width: 1,
        dashStyle: "Dot",
        zIndex: 2,
        label: paperRuleLabel(paperRuleText(chartData.average_title, paperEuros(cents / 100))),
    }] : []);

    Highcharts.chart("chart-incomes-expenses-container", {
        chart: { events: { render: paperFixEdges } },
        legend: { enabled: true },
        xAxis: paperCategoryAxis(chartData.categories),
        yAxis: {
            ...paperMoneyAxis(),
            plotLines: [
                ...average(chartData.incomes_average, "var(--skin-data)"),
                ...average(chartData.expenses_average, "var(--skin-harm)"),
            ],
        },
        tooltip: {
            shared: true,
            formatter() {
                const x = this.points[0].point.index;
                const row = (name, value) => `${name}: <b>${paperEuros(value)}</b><br>`;
                return `<b>${indexMonthName(chartData, x)}</b><br>`
                    + row(chartData.incomes_title, months.incomes[x])
                    + row(chartData.expenses_title, months.expenses[x])
                    + row(chartData.balance_title, months.balances[x]);
            },
        },
        series: [
            line(chartData.incomes_title, months.incomes, "var(--skin-data)", "circle"),
            line(chartData.expenses_title, months.expenses, "var(--skin-harm)", "diamond"),
        ],
    });
}
