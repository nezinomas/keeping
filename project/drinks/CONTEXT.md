# Drinks

Tracks a user's alcohol consumption against a yearly goal, and reports it back
as overview metrics, behaviour trends and harm-framing risk indicators.

## Language

### Consumption

**Std Av**:
The canonical unit of consumption — one Std Av is 10 g of pure alcohol. Every
amount is stored and computed in Std Av, whatever the user typed.
_Avoid_: unit, standard drink, UK unit

**Drink type**:
The kind of drink a user thinks in — beer, wine, vodka, or Std Av itself. It
fixes both the serving size a count refers to and the volume a millilitre
reading converts from.
_Avoid_: option, category, beverage

**Drink**:
One amount recorded on one date.
_Avoid_: entry, record, log, counter

**Drink Quantity**:
An amount of a Drink type: canonical in Std Av, and aware of whether it should
be read and shown as a volume in millilitres or as a count of pieces.
_Avoid_: stdav, ml, qty, measure

**Consumption Year**:
One user's Drinks for one calendar year, in canonical units, together with that
year's Drink Target and its reach back into the year before.
_Avoid_: period, dataset, year data

**Year boundary**:
How far into a year a metric may read: today while the year is still running,
Dec 31 once it is over — and, for the year before it, only as far as the same
month and day. One rule, shared by every lib that reports a year.
_Avoid_: cutoff, year end, clipping

**Year Comparison**:
Average daily consumption of several years plotted side by side. Years with no
Drinks drop out rather than showing as a flat line.
_Avoid_: history chart, multi-year

**Drinking day**:
A calendar day with at least one Drink recorded. The counterpart to Dry days.
_Avoid_: active day, wet day, session

**Intensity**:
Std Av per Drinking day: a year's total divided by the days it was actually
spread over, not by the days in the year. Stays in Std Av whatever Drink type is
selected, because it is read against the Heavy day threshold.
_Avoid_: average, per-day, strength

**Weekday profile**:
One year's consumption resolved by day of the week, as both a Drinking-day rate
and an Intensity. Each weekday is divided by how many times it has come round,
not by the days in the year.
_Avoid_: weekly pattern (that reads as the Risk tab's per-week totals), day
breakdown

**Typical year**:
Twelve months as both a Drinking-day rate and an Intensity — the same kind of
shape as the Weekday profile, one period longer, and no year axis at all. Always
draws the year the header selects; draws a Pooled range behind it once the user
asks for one. Only years carrying a Drink contribute days to the denominator.
_Avoid_: average year, seasonality, monthly totals (that is `sum_by_month`)

**Profile layer**:
One span of time on a profile chart: its Drinking-day rate, its Intensity, and
the label naming the span. Layers are ordered back to front, and the front one
is the reading the chart is about. The Weekday profile has one, unlabelled,
because its Tab already names the year; the Typical year has two.
_Avoid_: series, dataset, overlay

**Pooled range**:
The from-year and to-year the Typical year's back layer is drawn from. The
user's choice, never the app's: it is what keeps a month-per-row era out of the
profile without the app deciding whose years to trust, and nothing is pooled
until they press for it. Always named on the layer it produced.
_Avoid_: filter, period, span

### Goals

**Drink Target**:
The maximum daily volume a user sets for one year. At most one per user per
year. Stored in Std Av, so it is re-expressed in whichever Drink type is being
viewed — the same target reads as 500 ml of beer or 234 ml of wine.
_Avoid_: goal, limit, quota, budget

### Risk

**Heavy day**:
A day whose total exceeds 6 Std Av — roughly 60 g of alcohol. A daily total,
not a single-occasion measure.
_Avoid_: binge, bad day

**Low-risk guideline**:
11.2 Std Av in a week, the UK CMO guideline restated in Std Av. Weeks above it
are counted as over guideline.
_Avoid_: safe limit, recommended limit

**High-risk threshold**:
28.0 Std Av in a week, the upper marker a week is measured against.
_Avoid_: danger zone, max

**Dry days**:
Consecutive days since the last recorded Drink.
_Avoid_: gap, streak, sober days

### Presentation

**Tab**:
One of the six drinks views — Overview, Habits, Trends, Risk, History, Data. Each
is fetched and reloaded independently.
_Avoid_: page, panel, screen

**Habits tab**:
The drinks view for recurring shape — which days, how intensely, what a typical
year looks like — as opposed to level (Overview), direction (Trends) or harm
(Risk). English
`msgid` `Habits`, Lithuanian `Įpročiai`.
_Avoid_: Weeks (the Risk tab owns weekly vocabulary), Patterns, Rhythm

**Recent day**:
One of the last five calendar days, offered in the quick-add sheet as Today,
Yesterday and three weekday names. Always the real calendar day, never shifted
into the year being browsed.
_Avoid_: date option, day offset

**Stat Card**:
One summary tile on a Tab: a title, a value, the unit that value is read in, a
note, and how to colour them. The tone and arrow are resolved before it reaches
a template — a Tab's own vocabulary (a risk band, a year-over-year direction, a
metric against a Drink Target) never reaches the markup. So is the unit: it is
set at a third of the figure's size, so it is carried beside the value rather
than inside it, and a card whose figure is read as typed carries none. Nothing
frames a Stat Card and nothing rules between two of them — the figures are
centred in whitespace, and the only line is the short one over the note.
_Avoid_: trend card, widget, KPI, metric box

**Paper skin**:
The visual language every Tab wears: a white ground, chrome in ink, hairline
Panels, figures in a condensed display face and every label in mono. It is
scoped to the `.drinks-skin` wrapper `index.html` puts around every Tab, so no
other app inherits it; the `--skin-*` tokens it is built from are declared on
`:root` instead, because Highcharts renders a tooltip outside that wrapper and a
token it cannot resolve there is drawn black. Lives in `apps/_drinks.scss` and
`chart_drinks_paper.js`, and nothing about it belongs in a core palette variable.
_Avoid_: theme, style, look, design system

**Data hue**:
The one colour a reading is drawn in. Chrome carries no hue at all, so the only
colour on a Tab is the data's. Two measures on one chart — the Weekday profile's
rate and Intensity — take the Data hue and one second hue; several spans of the
*same* measure, like a 7-day average against a 30-day one or one year against
the next, take steps of the Data hue rather than hues of their own, because they
are one metric read over ordered spans.
_Avoid_: primary colour, accent, blue, series colour

**Harm**:
The colour a reading takes for being harmful, and nothing else: the part of a
month over the Drink Target, a week over the Low-risk guideline, a Heavy day. It
has two steps, guideline and threshold, so a week over one is not drawn as a week
over the other. Nothing under a limit is coloured for being under it — there is
no green on a Tab, because staying inside a limit is the baseline, not an
achievement.
_Avoid_: red, negative, danger, warning colour

**Panel**:
The hairline frame that a chart, the
calendar or a table sits in. The frame is the only thing separating it from the
page — a Panel has no fill and no shadow, and a Stat Card has no frame at all.
_Avoid_: card, box, tile, container
