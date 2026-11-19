# Debts

Records money the user lent to someone or borrowed from someone, and the money returned
against it. What debts add to a year's figures is Bookkeeping's (its Index); this page
lists the records.

## Language

**Debt**:
A `Debt`: a sum lent or borrowed on a date, from an Account, to or from an Other party.
Its Debt type never changes after it is saved. *Skola*.
_Avoid_: loan (in code), credit

**Debt type**:
Which way the money went (`Debt.debt_type`): **Lend** (`lend`, *Paskolinta*), the user
gave it; **Borrow** (`borrow`, *Pasiskolinta*), the user took it. Every form route
names it; a Tab's path names only Borrow (`borrow/`), Lend's tabs sit at the root.
_Avoid_: direction, kind

**Other party**:
Who the Debt is with (`Debt.name`): the *Borrower* (*Paskolos gavėjas*) of a Lend, the
*Lender* (*Paskolos davėjas*) of a Borrow. An open Debt may not take a name another Debt of
its type already holds.
_Avoid_: person, contact, title

**Return**:
A `DebtReturn`: a sum paid back against one Debt, on a date, into or out of an Account.
Lend returns read *Grąžino*, Borrow returns *Grąžinau*. Never more than the Debt's
Remaining; never dated before its Debt.
_Avoid_: repayment (in code), payment

**Returned**:
The sum of a Debt's Returns (`Debt.returned`), kept by the DebtReturn signal. *Grąžinta*.

**Remaining**:
What is still owed on a Debt: its sum less its Returned. *Liko*.
_Avoid_: balance, left

**Closed**:
A Debt the user marked fully returned (`Debt.closed`); allowed only when Remaining is 0.
A Closed Debt shows only in its own year, and its Returns can no longer be edited or
deleted. An open Debt shows in its own year and every later one. Labelled *Grąžinta*.
_Avoid_: settled, paid off, done

**Tab**:
One of the page's four lists: *Paskolinta · Grąžino · Pasiskolinta · Grąžinau*.
