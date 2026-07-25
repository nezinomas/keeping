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

**Year Comparison**:
Average daily consumption of several years plotted side by side. Years with no
Drinks drop out rather than showing as a flat line.
_Avoid_: history chart, multi-year

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
One of the five drinks views — Overview, Trends, Risk, History, Data. Each is
fetched and reloaded independently.
_Avoid_: page, panel, screen

**Stat Card**:
One summary tile on a Tab: a title, a value, a note, and how to colour them.
The tone and arrow are resolved before it reaches a template — a Tab's own
vocabulary (a risk band, a year-over-year direction, a metric against a Drink
Target) never reaches the markup.
_Avoid_: trend card, widget, KPI, metric box
