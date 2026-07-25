# Context Map

## Contexts

- [Drinks](./project/drinks/CONTEXT.md) — records alcohol consumption and reports it against a yearly goal

The remaining apps under `project/` (accounts, bookkeeping, books, counts, debts,
expenses, incomes, journals, pensions, plans, savings, transactions, users) have
no glossary yet. Their absence here means "not modelled", not "no domain".

## Relationships

- **Users → Drinks**: a User carries the Drink type they are currently viewing in and the year they are working in; Drinks reads both and never asks for them separately
- **Core → Drinks**: Drinks renders its calendar heatmap through the shared calendar grid in `project/core`, which the Counts context also uses
