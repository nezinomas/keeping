from dataclasses import dataclass


@dataclass(frozen=True)
class WealthDto:
    account_balance: int
    saving_balance: int
    pension_balance: int
