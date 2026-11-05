# Core

The pieces every paper page shares. Only what a page renders or reads today is named here.

## Language

### Page shape

**Panel**:
A block on a paper page: its Panel title, an optional subtitle, then a chart, a
Calendar, a ruler or a table. `<c-panel title="…">`. A Panel that holds a figure is
framed, because a plot has no edge of its own.
_Avoid_: card, box, widget, section

**Panel title**:
The display-face title, written as in a sentence, that opens a Panel, an HTML `<h2 class="panel__title">`. A chart
inside the Panel sets no title of its own.
_Avoid_: header, heading, chart title

**Table Panel**:
A Panel whose content is a table: `<c-panel table title="…">`. It keeps its Panel
title, subtitle and id, and has no frame, because the table's header band and rules
already give it structure. A tab whose one listing is a table has no Panel at all.
The rule for a new page:
[paper-migration §11](../../.plans/playbooks/paper-migration.md).
_Avoid_: bare panel, frameless panel, table card

**Sort header**:
A table's head cell that orders the table by its column: a link to the table's url
with `order=<key>`, plain text when that order is the one shown. `<c-sort-th>` takes a
state, never a class: `align="left"`, or `column="title"` / `column="total"` for a
Month table's first and last columns.
_Avoid_: sortable th, sort link, column header

**Quick-add**:
The bar at the foot of an app's paper page, outside the swapped tab: the day of year and
the pills that open the app's add forms (`<c-quick-add.pill>`, or `<c-quick-add.link>`
for a page of its own). A pill shown on one tab only takes `tab="<name>"`.
_Avoid_: add buttons, action bar, FAB

**Overview**:
A ledger app's first tab (Incomes, Expenses): three stat cards — this year, per month,
largest type — above a Panel charting this year's months against last year's, both to
the Year boundary. `Overview.build` in [`core.lib.overview_cards`](lib/overview_cards.py)
makes both; the app gives its service, its type field and its largest-type explanation.
_Avoid_: dashboard, summary, Apžvalga in code

**Type table**:
A ledger app's Rūšys tab (Incomes, Expenses): one row per type, this year, last year,
share of the year and last date, with a total row. [`core.lib.type_table`](lib/type_table.py)
holds the columns, the pk-keyed figures, the cells and the total; `TypeOrder` takes the
app's last-date key (`last_income`, `last_expense`), and the app adds its own rows.
_Avoid_: category table, summary table

### Time

**Selected year**:
The year the header's year menu selects, kept on the User
(`User.selected_year()`); every page reads its figures for it. The first login sets it
to the current year; it is not necessarily the current one.
_Avoid_: current year, user year, active year

**Year boundary**:
How far into a year a metric may read: today while the year is still running,
Dec 31 once it is over, nothing yet for a Coming year — and, for the year before it,
only as far as the same month and day (today, for a Coming year). The rule lives in [`core.lib.year_boundary`](lib/year_boundary.py);
every app that reports a year reads it there. Do not re-derive it.
_Avoid_: cutoff, year end, clipping

**Coming year**:
A Selected year after today's: the year menu offers the next one so records can be
dated ahead. None of it has passed, so a figure per day or per week has nothing to read;
its records still list.
_Avoid_: future year, next year

### Data

**Model service**:
An app's read gateway to one model, scoped to the user's journal:
`get_queryset()` holds the scope, `items()` the rows a page lists, and
`year(year)` a year's rows for a dated one (`DatedModelService`). It is
built from a real user only: `BaseModelService.__init__`
([`core.services.model_services`](services/model_services.py)) refuses a
missing or anonymous one, so a subclass adds no user check of its own.
_Avoid_: manager, repository, DAO
