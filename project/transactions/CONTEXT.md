# Transactions

Records money a user moves between their own places: account to account, a fund
into an account, a fund into another fund. Nothing here is earned or spent; each
Move leaves one owner's balance and enters another's. The page also lists the
user's Accounts, which have no page of their own.

## Language

### Owners

**Account**:
Where money sits outside a fund — a bank account, cash. Ordered by `order`, then
title. May be closed in a year (`closed`, its Close year in
[bookkeeping/CONTEXT.md](../bookkeeping/CONTEXT.md)); empty means open. *Sąskaita*.
_Avoid_: wallet, bank, source

**Fund**:
A `SavingType` — shares, a fund or a pension fund the user saves into; owned by the
Savings app, only moved out of here. May be closed in a year, as an Account. *Fondas*.
_Avoid_: saving type (in prose), investment, portfolio

### Moves

**Move**:
Any of the three records below: a date, a from-owner, a to-owner and an Amount.
The abstract model `Move`.
_Avoid_: transaction (for the three together), transfer, row, entry

**Transaction**:
A Move from one Account to another. No Fee. *Pinigų pervedimas*; its list is the
*Pervedimai* tab.
_Avoid_: transfer, payment

**Fund sale**:
A Move out of a Fund into an Account (`SavingClose`), with a Fee. Its form can close
the Fund. The form's title stays *Fondas ⇒ Sąskaita*.
_Avoid_: saving close (in prose), withdrawal, redemption

**Fund switch**:
A Move out of one Fund into another (`SavingChange`), with a Fee. Its form can close
the Fund it leaves. The form's title stays *Fondas ⇔ Fondas*.
_Avoid_: saving change (in prose), swap, exchange, transfer

**Amount**:
What a Move carries, in cents (`price`). *Suma*.
_Avoid_: price (in prose), sum, value

**Fee**:
What a Fund sale or Fund switch cost on top of its Amount, in cents (`fee`,
default 0). *Mokesčiai*.
_Avoid_: commission, charge, cost

**Close rule**:
What the form's close box tells the Fund a Move leaves: keep its Close year, close it
in the Move's year, or reopen it (`close_rules.py`). Read once by the receiver.
_Avoid_: close flag, close checkbox

### The page

**Tab**:
One of the page's four lists — Transactions, Fund sales, Fund switches, Accounts —
one kind of record each; Transactions opens first. The navbar's *Pervedimai* item
names all four, so Accounts are found without knowing they live here.
_Avoid_: page, section, view, panel

**Closed accounts**:
The Accounts Tab's second table, of the Accounts closed before the viewed year: struck
through, captioned *uždaryta* and its year, oldest close first. Folded below the open
ones — the Accounts open in the viewed year, not closed or closed that year or later —
until the *Uždarytos sąskaitos* switch unfolds it; the Tab has one URL.
_Avoid_: scope, filter, show closed, archive

**Close mark**:
*Uždaryta* beside the Fund on the Fund sale or Fund switch that closed it — the move
whose form opens with the close box ticked (`FundCloseYear.is_closing_move`). A state
in ink, never a row colour.
_Avoid_: closed badge, closed flag

No Cards: the app shows no figures of its own (user, 2026-11-01). Its sums already
live in Bookkeeping. The Tabs are *Pervedimai · Fondų pardavimai · Fondų keitimai ·
Sąskaitos*. Design: `.plans/evidence/2026-11-01-transactions-paper-skin/design.md`.
