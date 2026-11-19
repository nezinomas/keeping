# Expenses

Records what a user spends, one Expense per type and name per purchase, and — for
shops that hand out a PDF — reads that PDF back into Expenses, remembering by
Keyword which Expense name each product belongs to.

## Language

### Recording

**Expense type**:
The top-level heading an Expense is filed under — Maistas, Buitinės, Sveikata.
One per journal per title.
_Avoid_: category, group, parent

**Expense name**:
The heading inside an Expense type — Pieno produkai, Daržovės. May be limited to
one year (`valid_for`); a name limited to another year does not exist for that year's
Expenses, though Rūšys lists it with its year.
_Avoid_: subcategory, item, product

**Expense**:
Money spent on one date, from one account, under one Expense name, with a
quantity. When it comes from a Receipt it is an Expense group, saved.
_Avoid_: purchase, transaction, row

**Exception**:
An Expense flagged `exception` — spent outside the usual run of the year. Marked by an
ink rule on its date.
_Avoid_: outlier, special, flagged row

### The page

**Tab**:
One of the page's three views of the year — Apžvalga, Duomenys or Rūšys; Apžvalga
opens first.
_Avoid_: page, section, view, panel

**Month filter**:
Which month Duomenys lists, or all of them (*Visi įrašai*); carried in the URL.
_Avoid_: month tab, month button, period, month 13


### Importing a Receipt

**Receipt**:
A shop's document of one purchase — Barbora's *lydraštis*, Maxima's e-receipt as
Gmail prints it — read into Receipt lines, the total the shop printed as the sum to
pay, and any Shop money. It **agrees** when its lines add up to that total plus the
Shop money; one that does not is shown with the difference, never refused.
_Avoid_: invoice, bill, pdf, order, check

**Receipt line**:
One product on a Receipt: its title as the shop prints it, the amount collected —
a whole number, where a weighed product counts as 1 and its weight is not kept —
and its price in cents after every Item discount. The Review may correct its
title, amount and price.
_Avoid_: item, row, product, entry

**Unit**:
How the shop measures a line — **pieces** (`vnt`) or **weight** (`kg`). Used only
while reading: pieces give their count, weight gives 1.
_Avoid_: measure, uom

**Deposit line**:
A Receipt line for a bottle or can deposit (`UŽSTATAS`). It is mapped like any
line, and adds its price to the group — never its amount to the quantity.
_Avoid_: pant, užstatas, return

**Item discount**:
A discount the shop prints against one product (Maxima's *AČIŪ nuolaida
prekei:*). It is not a Receipt line: it is taken off the product line directly
above it.
_Avoid_: rebate, promo, discount line

**Shop money**:
The part of a Receipt paid with the shop's own money (Maxima's *MAXIMOS
pinigai*), in cents; 0 on a Receipt that shows none. Money the purchase *earns* is
not Shop money and is not read.
_Avoid_: loyalty payment, points, bonus, cashback

**Shop money line**:
The one Receipt line the user picks in the Review to carry the Shop money — its
price is lowered by it on Import, so the Expenses add up to what was paid. It is
never skipped and never lowered to zero or below.
_Avoid_: carrier, discount target

**Shop layout**:
The facts about one shop's Receipt and nothing else — the text that identifies it,
where its lines are and how they are told apart, the labels of its total and Shop
money, any unit or deposit words beyond the shared ones. Data, not code: a
`TableLayout` for a shop that prints a table, a `TextLayout` for one that prints
text lines.
_Avoid_: config, template, format, profile

**Shop parser**:
Turns a PDF into a Receipt and recognises, from the PDF's text, the ones it can
read. A PDF no parser recognises is an error, not an empty Receipt. Every Shop
parser shares the converters; only how it finds the lines differs.
_Avoid_: reader, extractor, importer

**Table parser**:
The Shop parser for any shop whose Receipt lines are a table, driven entirely by a
`TableLayout`. It names no shop. Barbora is read by it.
_Avoid_: generic parser, default parser

**Watermark**:
Letters stamped across a Receipt's page that are not its print — Barbora's grey
diagonal *N-20* on an order with age-restricted goods. The Table parser drops any
letter drawn askew or 50pt or larger before it reads the table.
_Avoid_: stamp, overlay

**Text parser**:
The Shop parser for any shop whose Receipt lines are lines of text, driven entirely
by a `TextLayout`. It names no shop. Maxima in-store is read by it.
_Avoid_: line parser, plain parser

**Keyword**:
A lower-case stem, per journal, pointing to one Expense name — `jogurt` →
Pieno produkai. Typed by the user in the Review; at least 3 characters and found
in the title of the line it was typed on.
_Avoid_: tag, rule, alias, memory, mapping

**Match**:
The longest Keyword found in a line's title, case-insensitively, whose Expense
name exists for the import year. Diacritics must agree. A line with no Match is
**unmatched** and comes to the Review blank — nothing is guessed.
_Avoid_: suggestion, guess, hit

**Review**:
The table between reading a Receipt and saving it: each line either takes an
Expense type, Expense name and Keyword, or is skipped; its title, amount and price
may be corrected; and, when the Receipt has Shop money, one line is the Shop money
line. It shows whether the Receipt agrees, live, and saves either way.
_Avoid_: preview, confirm, mapping screen

**Open line**:
A Review row still waiting for the user: not skipped, and no Expense name chosen.
Every unmatched line starts open; a matched line becomes open if its name is
cleared. The only thing in the app coloured for being empty — it wears the
attention wash until it is filled in or skipped.
_Avoid_: unmatched row, missing, todo, error row

**Expense group**:
The reviewed lines sharing one Expense name. Its price is the sum of their prices;
its quantity is the sum of their amounts, Deposit lines adding nothing — and never
less than 1.
_Avoid_: bucket, aggregate, bundle

**Import**:
Saving a Review: the Shop money taken off the Shop money line, one Expense per
Expense group, and every Keyword the Review holds written or re-pointed — the last choice wins. All of it or none of it.
_Avoid_: upload, sync, commit

## Relationships

- A **Receipt** holds many **Receipt lines**; a **Shop parser** produces it from a PDF.
- A **Table parser** or a **Text parser** is a **Shop parser** given one **Shop layout**; one per shop.
- A **Receipt** may carry **Shop money**; the **Review** puts it on one **Shop money line**.
- An **Item discount** belongs to the **Receipt line** above it and is folded into its price.
- A **Keyword** points to one **Expense name**; an **Expense name** has many Keywords.
- A **Match** is found per **Receipt line**; the **Review** shows it, the user may override it.
- An **Import** turns the **Review**'s non-skipped lines into **Expense groups**, one **Expense** each.
