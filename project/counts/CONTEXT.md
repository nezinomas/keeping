# Counts

Tracks anything a user decides to keep a tally of — one Counter per thing,
Records dated against it — and reports back the year's level, its recurring
shape, and its history.

Only what the app has, or is being built now, is named here. A metric nobody
reports yet gets its glossary entry with the ticket that builds it, not before.

## Language

### Recording

**Counter**:
One named thing a user tracks, with its own page and its own Records. A user
makes as many as they like, and the app never asks what one is for. `CountType`
is the model's name and stays; the word in the UI and in prose is Counter.
_Avoid_: count type, category, tracker, habit, metric

**Record**:
One Quantity on one date, against one Counter. `Count` is the model's name and
stays. A date may carry more than one, so a count of Records is not a count of
days.
_Avoid_: count, entry, log, event, occurrence

**Quantity**:
How much one Record carries. It is a real amount and it is summed — a Counter
whose Records are all 1 is counting occurrences, and the app does not treat that
as a separate kind of Counter. It has no unit: what a Quantity of 3 means is the
user's business, so nothing in the app labels one.
_Avoid_: amount, value, count, units

**Counter year**:
One user's Records for one Counter in one calendar year — the year the header
selects, not necessarily the current one.
_Avoid_: period, dataset, year data

**Lifetime figure**:
A reading taken over every Record a Counter has, not over the Counter year. It is
what lets a Counter recording three times a year say anything at all: two Gaps
support no median, where thirty-six do.

**Which of the two scales leads is the Tab's decision, not the figure's.** On
Overview and History the value states the year and the Lifetime figure is its
note — *63 d · įprastai 82 d.* On Periodicity, whose window is the whole life,
the Lifetime figure is the value and the year is the note — *82 d · šiemet: 114*.
Either way both are on the Card, because neither means much alone.
_Avoid_: all time, overall, global, pooled

**Year boundary**:
How far into a year a metric may read; defined in [core](../core/CONTEXT.md).
_Avoid_: cutoff, year end, clipping

### Rhythm

**Gap**:
The number of days between two consecutive Records, bounded by a Record at each
end. The first Gap of a Counter year reaches back to the last Record of the year
before, so January is not measured from Jan 1.
_Avoid_: interval, break, streak, period

**Current gap**:
Days since the last Record. It is open, so it is not a Gap: it never enters the
Longest gap or the Median gap, or a Counter left alone would set a new record
every day. Only a year still running has one. It is read beside the Typical gap,
which is what makes it mean anything.
_Avoid_: last time, days since, streak, dry days

**Longest gap**, **Median gap**:
Of the completed Gaps in the Counter year. Neither is judged — a long Gap is not
a failure and a short one is not an achievement, because the app does not know
what the Counter is for. The median rather than the mean: one long absence drags
a mean and says nothing about the rhythm.
_Avoid_: worst gap, best gap, average gap

**Typical gap**:
The median of every Gap the Counter has ever had. It is the Lifetime figure the
year's own Gaps are read against, and the only one of them that survives a
Counter recording three times a year — a year holding two Gaps has no median
worth the name, where thirteen years hold thirty-six.
_Avoid_: average gap, normal, expected, usual

**Rate**:
Records per year over the Counter's whole life. Per year, not per month: a
Counter recording three times a year reads as 0.25 a month, and the figure exists
to say whether the year on view is an ordinary one — which needs a denominator
wide enough to have an ordinary.
_Avoid_: frequency, per month, ratio, average

**Weekday profile**, **Monthly profile**:
Every Record a Counter has, resolved by day of the week and by month — pooled, not
one year at a time, because one year of a Counter used three times is seven bars
of nothing much. The same kind of object the Drinks glossary names with the same
words, and nothing here contradicts them.
_Avoid_: weekly pattern, breakdown, seasonality

**Gap distribution**:
How many Gaps of each length a Counter has had, over its whole life and **in
bins** — the reading that says a Counter has a rhythm at all. One bar per distinct
length is not this: it draws a Counter's twenty-seven single occurrences and hides
the one length that happened six times. Bin edges come from that Counter's own
Gaps, never from a constant, and the chart names them.
_Avoid_: histogram (that is the chart type, not the reading), frequency

### Presentation

**Tab**:
One of the four counts views — Overview, Periodicity, History, Data. Each is
fetched and reloaded independently, and each belongs to one Counter. The row they
sit in is not this app's: it is the shared secondary nav every redesigned app
wears, `skin/_subnav.scss`, identical to the one Drinks draws. Anything the row
needs is written there for both, never here for one.
_Avoid_: page, panel, screen

**Overview tab**:
The Counter year's level: what it came to, how many Records made it, how long
since the last one, and the Calendar those three describe.
_Avoid_: index, charts, summary

**Periodicity tab**:
The Counter's recurring shape — which weekdays, which months, how far apart —
read over **every Record it has**, not over the Counter year. It is the one Tab
whose window is the whole life, and the year appears on it only as a note. That
is not a preference: a Counter used three times in a year draws three bars of one
and says nothing, where twelve years of the same Counter draw a rota. Every chart
on it captions the span it pooled.

English `msgid` `Periodicity`, Lithuanian `Periodiškumas`. Named for the reading
rather than for the user: a Counter may record something chosen or something that
simply happens, and *Habits* would claim the first.
_Avoid_: Habits, Rhythm, Gaps, Patterns

**History tab**:
Every year the Counter has, side by side. The one Tab that is not about the year
the header selects.
_Avoid_: all time, archive, years

**Card**:
One figure on a Tab. Counts uses the shared
[`StatCard`](../core/lib/stat_card.py) in its plain and empty forms only — no
tone, no arrow, no comparison, no pencil. Nothing is coloured for being high or
low, because a Counter has no direction the app can know: a Counter of
donations wants a short Gap and a Counter of relapses wants a long one, and
nothing stored says which this is. A Card with nothing to show is an em dash and
a note, never a zero.

Three parts, and a Card carries only the ones it needs — the shape Drinks' Cards
already have:

- **A short title.** Two or three words, written as in a sentence. *Tarpas*, not *Dienos
  nuo paskutinio įrašo* — whatever will not fit is the explanation's job, not the
  title's.
- **An explanation**, behind the ⓘ beside the figure, and **only where the short
  title leaves a real question**: which denominator, median or mean, what exactly is
  being counted. A card whose title says it all carries no mark.
- **A note**, and only when there is a Lifetime figure to read the value against or
  a span to name. It never restates the value, and it never says whether the value
  is good — *63 d · typically 82 d* is two facts, and which the reader prefers is
  theirs to decide.

Counts uses no arrow, no unit and no pencil: it has no direction to point, a
Quantity has no unit, and there is nothing on a Card the app can edit.
_Avoid_: widget, KPI, tile, trend card, info row

**Calendar**:
The year drawn as a grid of days, one column a week, one block a month —
[`<c-calendar>`](../core/templates/cotton/calendar.html), shared with Drinks. It
answers *which days*. In Counts it draws **presence**: a day either carries a
Record or it does not, at one level, in the Data hue at full strength — a Counter
with three Records in a year has three marks to find, and a pale one cannot be
found. Drinks passes thresholds and gets four levels; Counts passes none, because
a Quantity has no unit here and no threshold to be read against.
_Avoid_: heatmap, heat grid, activity graph

**Gap strip**:
The same year drawn as one band of 365 days, in the Calendar's panel and beneath
it, answering *how far apart* — a Gap becomes a length you measure rather than
cells you count. Both are always drawn. The app never picks one by how much data
a year holds: any such rule draws the same Counter two different ways in
consecutive years, and would withhold the Calendar from exactly the sparse
Counter whose whitespace is the reading. It is this app's own, not the shared
component's: a Counter with a Record most days draws a solid bar, and Drinks
would only ever draw that one.
_Avoid_: timeline, barcode, sparkline, ruler

**Counter menu**:
The control beside the Add record pill, naming the open Counter — the same place
and the same shape as the Drink type switcher in Drinks, in a bar fixed at the
foot of the page. It lists every Counter the user has, and under a divider the
three acts that are about a Counter rather than about a Record: rename this one,
delete this one, make a new one. Named a menu and not a switcher because
switching is only half of it, and someone looking for delete will not open a
control called a switcher.

It is also **the only place the page names the Counter**. There is no page header
and the Tab row holds nothing but Tabs: a site nav, the Tabs and the content,
exactly as Drinks — a third bar existed only to repeat what this pill already
says, and the bar is fixed, so the name is on screen wherever the page is
scrolled to. Nothing about a Counter is edited anywhere else either, so a page
opened to read data holds no control that can destroy it.
_Avoid_: counter switcher, header, title, dropdown, picker, filter

**Delete a Counter**:
Deleting a Counter deletes every Record in it, because `Count.count_type`
cascades. So the confirmation names what goes — the record count and the year the
first one was made — and does not proceed until the Counter's title is typed. That
ceremony belongs to the Counter alone: deleting one Record is a trash icon in its
row and asks nothing, because one Record is one line and it can be typed again.
_Avoid_: remove, archive, clear

**Add record**:
The pill in the core quick-add bar at the foot of the page that opens the record
form, with the Counter menu beside it. Named for the act. It opens the modal that
already exists rather than submitting on its own, the same call Books' **Add book**
makes — so the bar holds a control and a pill, and no sheet above them.
_Avoid_: new button, floating button

**Paper skin**:
The visual language every Tab wears — a white ground, chrome in ink, hairline
Panels, chrome in a condensed display face and what the user reads in the body face.
Scoped to
the `.paper-skin` wrapper, built from the `--skin-*` tokens on `:root`, and
shared with Drinks and Books; it lives in `sass/sass/skin/` and `chart_paper.js`
and none of it is this app's. `apps/_counts.scss` holds only the markup Counts
alone renders.
_Avoid_: theme, style, look, design system

**Data hue**:
The one colour a reading is drawn in. Chrome carries no hue at all, so the only
colour on a Tab is the data's — and in Counts that is the whole palette, because
there is no harm here to reserve a second hue for.
_Avoid_: primary colour, accent, series colour
