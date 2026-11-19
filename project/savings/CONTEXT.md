# Savings

Records money a user puts into what they save in: funds and shares (`savings`), and the
II pillar pension (`pensions`, which has no page of its own and is shown here). What a
saving is worth and what it earned is Bookkeeping's (its Savings summaries, Index and
Detailed); this page lists the records and the funds they go into.

## Language

### Owners

**Fund**:
A `SavingType`: shares, a fund or a III pillar pension fund the user saves into. Has a
Fund kind and a Fee source. May be closed in a year (`closed`, its Close year in
[bookkeeping/CONTEXT.md](../bookkeeping/CONTEXT.md)); empty means open. Money leaves it
only by a Fund sale or Fund switch ([transactions/CONTEXT.md](../transactions/CONTEXT.md)).
*Fondas*.
_Avoid_: saving type (in prose), investment, portfolio

**Fund kind**:
What a Fund is (`SavingType.type`): *Akcijos* (shares), *Fondai* (funds), *Pensijos*
(III pillar pension funds). Orders the Funds; not shown on the Funds Tab.
_Avoid_: type (in prose), category

**Fee source**:
Where a Fund's Fee is charged (`fee_source`): *iš investicijos* (from the money saved)
or *iš sąskaitos* (from the Account it came from).
_Avoid_: fee type

**Pension fund**:
A `PensionType`: the II pillar fund the user's pension goes into. Has a `closed`
column that nothing writes, so it is never closed (PEN-1). Shown as *II pakopos fondas*.
_Avoid_: pension type (in prose), Pensijos (that is a Fund kind)

### Records

**Saving**:
Money put into a Fund from an Account on a date (`Saving`): an Amount, a Fee, a remark.
*Taupymas*.
_Avoid_: deposit, contribution, investment, record (alone)

**Pension**:
Money put into a Pension fund on a date (`Pension`): an Amount, a Fee, a remark; no
Account. *II pakopa*.
_Avoid_: pension payment, contribution

**Amount**:
What a Saving or Pension puts in, in cents (`price`). *Suma*.
_Avoid_: price (in prose), sum, value

**Fee**:
What a Saving or Pension cost on top of its Amount, in cents (`fee`, default 0).
*Mokesčiai*.
_Avoid_: commission, charge

### The page

**Tab**:
One of the page's four lists — Savings, Funds, II pillar, II pillar funds
(*Taupymas · Fondai · II pakopa · II pakopos fondai*) — one kind of record each; Savings
opens first. The navbar's *Taupymas* item names all four.
_Avoid_: page, section, view, panel

**Closed funds**:
The Funds Tab's second table: the Funds closed before the viewed year,
struck through, captioned *uždaryta* and its year. Folded below the open ones — those
not closed, or closed in the viewed year or later — behind the *Uždaryti fondai*
button.
_Avoid_: archived, inactive, hidden funds
