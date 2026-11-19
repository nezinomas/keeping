# Plans

Holds what a user means to earn, spend and save in each month of a year, and
works out from it how much is left to spend per day. A Plan is an intention,
never a record: nothing here reads the Incomes, Expenses or Savings a user
actually booked.

## Language

### Planning

**Plan**:
The amount planned for one month of one Plan year, stored as integer cents in
`price`. Five kinds, one model each.
_Avoid_: budget, target, goal, forecast

**Plan year**:
One journal's Plans for the calendar year the header selects. A Plan covers the
whole year, so a per-month figure divides by 12, never by a Year boundary.
_Avoid_: period, budget year

**Income plan** / **Expense plan** / **Saving plan**:
A Plan against one Income type, Expense type or Saving type. An Expense plan is
*necessary* when its Expense type is (`ExpenseType.necessary`); Išlaidos shows the
necessary ones as *Būtinos išlaidos*, the rest as *Kasdienės išlaidos*.
_Avoid_: planned income, planned expense, planned saving

**Necessary plan**:
A titled Plan against an Expense type, kept outside the Expense plans for a cost
that is necessary but has no type of its own (UI *Papildomos būtinos išlaidos*).
_Avoid_: extra expense, additional plan, other

**Day plan**:
The amount the user means to spend per day in a month (the *Suma dienai* table).
Set against the Sum per day; above it, the month's plans do not fit.
_Avoid_: daily budget, day limit, allowance

### Calculations

**Calculations**:
The *Skaičiavimai* table, built by the `Calculations` service
(`plans/services/calculations.py`) in two blocks — *Kiek galiu išleisti per dieną*
(key `spend`) and *Patikra: ar telpa išlaidų planai* (key `check`) — derived month
by month from all five kinds of Plan. Read as one chain:
Pajamos − Būtinos išlaidos ir taupymas = Laisvi pinigai, ÷ days = Suma dienai.
The paper migration relabels and reorders them and changes no value.
_Avoid_: stats, summary, results

**Necessary expenses**:
*Būtinos išlaidos ir taupymas*: necessary Expense plans + Necessary plans +
**Saving plans**. Savings count as necessary here, but the Išlaidos *Būtinos* Card
leaves Saving plans out, so Būtinos + Kasdienės = Per metus.
_Avoid_: fixed costs, essentials

**Sum per day**:
*Suma dienai*: what the plans leave for each day of a month, after the necessary
expenses, out of the median Income plan.
_Avoid_: day budget, daily limit

**Residual**:
*Likutis*: what is left of a month once the Day plan is spent every day of it, the
cross-check of the Day plan the user entered: below zero exactly when the Day
plan is above the Sum per day. Also
a word users put in type titles (*Likutis*), which the table no longer marks.
_Avoid_: remainder, balance, leftover

### Presentation

**Tab**:
Pajamos, Išlaidos, Taupymas, Suma dienai — one `PlanTab` each. Suma dienai opens
by default, because it holds the outcome the other three feed.
_Avoid_: page, section, view

**This month**:
The current month number, read in whichever Plan year is selected: September
2026 shows September of 2027 when 2027 is open.
_Avoid_: current month (it is not the month of the selected year's boundary)
