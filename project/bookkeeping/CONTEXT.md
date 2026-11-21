# Bookkeeping

The year's money read across apps. What a page renders today is named here, and the
sync that writes the balance rows the pages read; Detailed is the first Bookkeeping
page on the paper skin. The Index section names the index page as its paper design
draws it (plan `bookkeeping-index-paper-skin`), ahead of the code that moves it.

## Language

### Index

**Index**:
The page at `/`: the selected year's money across apps — accounts, funds, pensions,
debts, the month balance — in four Index Tabs. Its navbar item and its page title draw
the selected year, the title with the open tab (`2026 | Apžvalga`); there is no
*Bookkeeping* label.
_Avoid_: home, dashboard, overview (*Apžvalga* is the Index's first tab, not the page;
core's Overview is a ledger app's first tab, a different block)

**Index Tab**:
One of the Index's four views, in this order: *Apžvalga* (opened by `/`; not core's
Overview): four Cards, the Account balances table, the Year strip, the No-incomes
table, the Debts table; *Fondai*: three Cards, the Funds table, the Pensions table;
*Balansas*: the Month balance table, then the Expenses-by-type table; *Grafikai*: the
expenses-by-type chart beside the balance-per-month chart (above it below 1200px), then
the incomes-and-expenses chart under both. Each is fetched and reloaded
whole, on every event that changes it; a closed tab reads fresh data when opened.
The Quick-add bar offers each Worth form as a pill on its own tab: *Sąskaitų faktas* on
Apžvalga, *Fondų faktas* and *Pensijų faktas* on Fondai. The refresh icon in the first
header cell of the Account balances, Funds and Pensions tables syncs every balance row
of every year and reloads the tab.
*Grafikai* also names a navbar item, a different page.
_Avoid_: section, panel, page

**Card**:
One figure at the head of an Index Tab, the skin's `StatCard`, in ink: whole euros.
Two figures differ: the Saved share is a percent, and a profit under 0,50 EUR either
way keeps its cents ("0,30", "-0,30"), so it never reads "0". No Card is a new
figure: each is one the page draws today. Apžvalga: *Pinigai* and *Turtas* (the wealth
service's, its accounts part the Account balances table's total), *Vidutinės
pajamos* and *Vidutinės išlaidos* (the year's averages, as the Month balance table's
average row). Fondai: the Saved share
(the savings service's, one decimal, the banner's figure before it), then
*Fondų pelnas* and *Pensijų pelnas*, the profit sum of the Funds table and of the
Pensions table, each with its percent as the note, one decimal. A figure of 0
(*Pinigai*, *Turtas*, an average in a running year with nothing in it) draws "–" as its
figure; one of these under 0,50 EUR either way rounds to a whole 0 and draws "0", never
"-0". A
Saved share of 0 draws "0,0". A Card with nothing to show draws the StatCard's empty
form: the Saved share in a year with no incomes, the two averages in a year not yet
started, *Fondų pelnas* and *Pensijų pelnas* when their table's total profit is zero
(no rows, no row with a fresh worth, or gains and losses that cancel); a loss draws its
figure with its minus. Fondai
always draws its three Cards.
_Avoid_: banner, tile, widget, KPI

**Worth check**:
An account's balance against its latest Worth, the Account balances table's *Delta*
column: positive green, negative `$harm`, and "ok" at zero, also green, the one zero
on paper that is not ink. The table's total row draws a dash at zero, not "ok".
_Avoid_: check alone (*Check* is the `latest_check` date; the Cash-flow check compares
two totals, not an account to its Worth), difference, deviation

**Cash-flow check**:
The year-end cash flow (the total row's *Pinigų srautas* cell in Balansas' Month
balance table) against the Account balances table's *Balansas* total (Apžvalga):
`mismatch` when the two differ, decided in Python. Each of the two cells is marked on its own tab, with
the attention wash and its "!". Account-charged fees count as in the sync.
_Avoid_: check alone (*Check* is the `latest_check` date; the Worth check compares one
account to its Worth, not two totals), balance check, reconciliation

**Saved share**:
What the year's Savings took of its incomes, in percent: the Savings into every Fund,
of every Fund kind (*Pensijos*, III pillar, included), over the incomes' total. A
Pension (II pillar) is not counted. The first Fondai Card, in plain ink at any value.
Computed in the savings service, not the template.
_Avoid_: savings rate, saved %, banner

**Account balances table**:
Apžvalga's Table Panel *Sąskaitos*: one row per account for the selected year, with
*pradžioje*, *Pajamos*, *Išlaidos*, *Balansas*, *Turiu* and the Worth check's *Delta*,
the account's latest Check in its tooltip, and a total row.
_Avoid_: accounts table (core's Owner table avoids it), Owner table (that lists
owners to open their edit forms)

**Funds table**:
Fondai's Table Panel *Fondai*: one row per Fund of every Fund kind but *Pensijos*
(*Akcijos*, *Fondai*), from their balance rows, with a total row whose profit is
*Fondų pelnas*.
_Avoid_: savings table, Owner table

**Pensions table**:
Fondai's Table Panel *Pensijos*: the Funds of kind *Pensijos* (III pillar) and the
Pension funds (II pillar) together, from their balance rows, with a total row whose
profit is *Pensijų pelnas*.
_Avoid_: II pillar table (it holds both pillars), Owner table

**Year strip**:
The Apžvalga line *2026 pradžioje / pabaigoje / Balansas*. *Pradžioje* is the
accounts' money carried into the year (their balance rows' past sum); *pabaigoje* is
the year-end cash flow, that start plus the year's flow, the same figure as the
Cash-flow check's Balansas cell, not an accounts total; *Balansas* is end less start.
It sits in a Panel titled with the selected year (*2026 metai*). The Forecast, under
the same three titles: its own Panel, drawn with the tab.
_Avoid_: summary, header row

**No-incomes table**:
Apžvalga's Table Panel *Be pajamų*: how long the money lasts without incomes. Rows:
the money, the months it lasts with spending unchanged, and after cutting the
unnecessary expenses; columns € + F and € + F + P, with the € / F / P legend. Its first
header cell reads *Nebūtinos išlaidos*, then the monthly sum those cuts save, muted,
then a "?" whose tip lists the cuts. A journal that marks nothing unnecessary draws a
muted "–" for the sum and no "?"; one whose marked expenses cost nothing in the six
months draws the "–" and the "?".
_Avoid_: no_incomes (that is the module), survival table

**Debts table**:
Apžvalga's Table Panel *Skolos*: one row per Debt type with an open Debt, *Paskolinta*
(lend) before *Pasiskolinta* (borrow); columns *Suma*, *Grąžinta* (Returned) and *Liko*
(Remaining), summed over every open Debt of that type, whatever its year, not the
selected year's; a Closed Debt is not counted. No open Debts, no Panel.
_Avoid_: debt mini-tables, borrow / lend tables

**Month balance table**:
Balansas' Table Panel *Balansas*: the year by month, a row per month (incomes,
expenses, balance, savings, the cash flow *Pinigų srautas*), then the average and
total rows, whose *Pinigų srautas* cell is the year-end cash flow. The average row
divides each column's sum over the months reached by their count: January to this
month while the year runs, all twelve once it is over, none before it starts; a later
month's rows count in the total, not in the average. *Rodyti skolas*
shows the debts' columns. A month-by-row table, not a Month table, so it has no
quarter band.
_Avoid_: year balance, Month table

**Expenses-by-type table**:
Balansas' Table Panel *Išlaidų statistika*: the year's expenses by expense type, a row
per month, a column per type, then the average and total rows, the average divided as
the Month balance table's, so the types' averages add up to its last cell. A month-by-row table,
not a Month table. How a type name too long for its column reads is the builder's
(design §5).
_Avoid_: year expenses (the include), Type table (Detailed's Išlaidos table, and core's
ledger Rūšys tab), expenses-by-type chart (Grafikai's chart of the year's totals)

**Current month**:
The month of today's date when the selected year is today's year; a past or a coming
year has none. Grafikai's two month charts draw its marks paler (the balance column,
each line's point), and its tooltip says *iki šiol*. A month after it, and every month
of a coming year, is a gap on both charts unless it already holds incomes or expenses,
which draw. Each line's average rule (*Vidurkis*) averages the months reached, the
current month included: all twelve for a past year, none for a coming one. An average
of nought, a coming year's or a year with no incomes, draws no rule.
_Avoid_: this month, open month, running month

### Detailed

**Detailed**:
The page at `/detailed/` (navbar *Detali*): the selected year's money by month, one
row per income type, saving type or expense name. Three Tabs — Pajamos, Taupymas,
Išlaidos — with Pajamos the default. A place to look a line up and to see where
the money goes; it reads no Year boundary and carries no threshold.
_Avoid_: breakdown, details, report

**Type table**:
One expense type's table on the Išlaidos tab: a Table Panel titled with the type
alone, a row per expense name. The Type tables come by their Total column, biggest
first, equal totals by type title. Its rows open by the Total column too, biggest
first; each re-sorts its rows on its own, independently of the others.
Pajamos and Taupymas each have one table and no Type table.
_Avoid_: category, category table, group

**Month table**:
The paper design of a table with twelve month columns: the title column sticky,
scrolling inside its container on a phone. `.month-table` in
`sass/sass/skin/_month_table.scss`; each month header names its month by the dictionary
abbreviation (*Saus.*) at every width, under a quarter band (`<c-quarter-band>`), as
`<c-month-headers>` does for Plans' plan and calculation tables. Detailed puts the same
list (`MONTH_ABBREVIATIONS` in `core/lib/translation.py`) each inside a `<c-sort-th>`.
_Avoid_: plans table, wide table, pivot

**Total column**:
The last column of a Month table on Detailed, *Viso*: a row's sum over the year, in
ink at weight 600 behind a thin rule. The row sum; the column sums are the total row
in `tfoot`.
_Avoid_: sum column, total_col (that is the data key, not the word)

**Share**:
A Type table's part of the Išlaidos tab's whole: its Total column over the sum of
every Type table's Total column, in the table's subtitle. Read as whole percent,
`< 1%` under half a percent, never `0%`, and `> 99%` from 99.5 % up to the whole; `100%`
only for the whole.
_Avoid_: percentage, weight, portion

### Sync

**Owner**:
What a balance row belongs to: an account, a fund (`SavingType`) or a pension type.
_Avoid_: category (that is the frame's `category_id`, not the word), type

**Balance row**:
One owner's money for one year: `AccountBalance`, `SavingBalance` or
`PensionBalance`. Derived, never entered: a save or delete of anything that moves
an owner's money re-syncs the whole journal's rows of that kind. An owner's years run
from its first row to the journal's last year plus one. A pension type's rows are built
like a fund's, by `SavingBalanceRows` in `lib/balance_rows.py`.
_Avoid_: balance table, snapshot, cache

**Close year**:
`closed` on an owner: the last year it has balance rows. Saving the owner re-syncs,
so closing drops its later years and reopening (`closed` empty) brings them back.
Empty means open.
_Avoid_: close date, end year, closing date

**Worth**:
A dated amount the user reads off an owner: `AccountWorth` (an account's *have*),
`SavingWorth` (a fund's market value), `PensionWorth`. Entered, unlike a balance row.
_Avoid_: valuation, snapshot, reading

**Check**:
`latest_check` on a balance row: the date of the owner's latest worth up to that
year. Empty means never checked, so years before an owner's first worth stay empty.
_Avoid_: check date, last update, Worth check and Cash-flow check (those compare
amounts; a Check is only a date)

**WIRING**:
The table in `tests/signals/test_signals_wiring.py`: for each sender, the receivers
one save and one delete reach (syncs, close year, first record), in call order. Who syncs what is read there, not
from the decorator stacks in `signals.py`.
_Avoid_: registry, signal map
