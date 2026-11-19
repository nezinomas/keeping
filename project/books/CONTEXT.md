# Books

Tracks the books a user reads against a yearly goal, and reports back how many
are finished, how many are still open, and how each year stood against its goal.

Only what the app has, or is being built now, is named here. A metric nobody
reports yet gets its glossary entry with the ticket that builds it, not before.

## Language

### Reading

**Book**:
One title, read once: an author, a title, the day it was started and — once it
is finished — the day it ended. A remark is optional and belongs to the reading,
not to the title. A title read twice is two Books and counts twice: the app
records readings, and nothing in it dedupes by author and title.
_Avoid_: entry, record, item, log

**Finished book**:
A Book with an end date. It counts in the year it *ended*, whatever year it was
started in, so a book carried across New Year belongs to the year it was
finished. English `msgid` `Finished`, Lithuanian `Perskaitytos`.
_Avoid_: readed, read book, completed, done

**Open book**:
A Book with no end date: started and not finished, however long ago. The app
does not judge how long that has been — nothing is called abandoned, stalled or
overdue, because the record cannot tell a slow read from a forgotten one. Its row
in the Book table is marked by its hair rules alone: being unfinished is a state,
so it is drawn in ink, not in the Data hue. The UI
label is the plainer English `msgid` `Reading`, Lithuanian `Skaitomos`; the word
in code, tests and prose is *open*, because *reading* names both the activity and
the book.
_Avoid_: reading (as a noun), current, active, in progress

**Reading year**:
One user's Books for one calendar year: the Finished books that ended in it, the
Open books started on or before it, and that year's Goal. It is the year the
header selects, not necessarily the current one.
_Avoid_: period, dataset, year data

### Goals

**Goal**:
How many books a user means to finish in one year. At most one per user per
year. It is a floor, not a ceiling — the opposite of Drinks' Drink Target — so
nothing is coloured for passing it, and nothing is coloured for falling short of
it either. `BookTarget` is the model's name and stays; the word in the UI and in
prose is Goal.
_Avoid_: limit, quota, plan, max, target (in prose)

### Presentation

**Tab**:
One of the two Books views — Overview (`index`) and Data (`data`). Each is fetched
and reloaded on its own.
_Avoid_: page, panel, screen

**Card**:
One number on the page, stated as recorded: a title and a value. Books uses the
shared `StatCard` in its plain and empty forms only — no arrow, no tone, no
comparison against last year — because the three figures it shows are facts about
the Reading year, not judgements of it. A figure carries no note: a note explains a
figure against something else, and these stand on their own. The order is
Finished, Reading, Goal — the year's count is the headline. A card with nothing to
show is an em dash and a note, never a zero.
_Avoid_: widget, KPI, tile, trend card

**Goal card**:
The Card that both states the Goal and edits it: a pencil in the card opens the
goal form — the year's own goal if it has one, a new one if it does not — and
the card reads as an em dash with *No goal set* until then. That is its only
note: a goal that exists is a number and nothing else. There is no Goal button
anywhere else on the page.
_Avoid_: goal button, target row, new goal

**Book table**:
Every Book the Reading year touches: the Finished books that ended in it, and
every Open book started on or before it. So a past year shows books that are
still open today — an Open book has no year of its own to be filed under. Rows
are ordered by the day they were started, newest first, not by the end date that
put a finished row there.
_Avoid_: list, records, data

**All records**:
The Book table widened to every year, paginated. Reached from the *All records*
item in the site nav's Books menu, which opens `data/all/` — there is no control
for it on the page itself. In the URL and the code it is the scope `all` beside
`year`, a name older than the idea. It widens the table and nothing else: the Cards and the chart read the Reading year
whichever endpoint drew the page.
_Avoid_: scope, filter, tab, view, all-time

**Search**:
Finding a book by author or title. It spans every year, because the year of a
book you are looking for by name is the thing you least reliably know. Reset is
what ends a search; nothing else narrows it back to one year.
_Avoid_: filter, query

**Finished by year**:
Every year's Finished count drawn against that year's Goal. English `msgid`
`Finished books`, Lithuanian `Perskaitytos knygos`. Years with no Finished book do
not appear, rather than drawing as a zero — including a year that had a Goal and
missed it entirely, whose goal therefore goes unshown. The chart reports what was
read, not what was intended.
_Avoid_: readed books, progress chart, history

**Add book**:
The pill in the core quick-add bar at the foot of the page that opens the book form.
Named for the act, not for the form or its position.
_Avoid_: new button, floating button
