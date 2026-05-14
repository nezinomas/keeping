from dataclasses import dataclass


@dataclass(frozen=True)
class WealthDto:
    account_balance: float
    saving_balance: float
    pension_balance: float
