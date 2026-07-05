"""Simple decumulation sequencer."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.models.investment_account import InvestmentAccount


@dataclass(frozen=True)
class DecumulationResult:
    withdrawals: dict[str, float]
    notes: list[str]
    unmet_need: float


def sequence_withdrawals(
    spending_need: float,
    accounts: list[InvestmentAccount],
) -> DecumulationResult:
    remaining = max(spending_need, 0.0)
    withdrawals: dict[str, float] = {}
    notes: list[str] = []
    order = ["taxable", "rrsp", "tfsa", "fhsa", "hisa", "rrif"]
    accounts_by_type = sorted(accounts, key=lambda acct: order.index(acct.account_type.lower()) if acct.account_type.lower() in order else 99)
    for account in accounts_by_type:
        if remaining <= 0:
            break
        amount = min(account.current_balance, remaining)
        if amount <= 0:
            continue
        account.current_balance -= amount
        withdrawals[account.account_type] = withdrawals.get(account.account_type, 0.0) + round(amount, 2)
        remaining -= amount
        notes.append(f"Withdrew {amount:.2f} from {account.account_type}.")
    if remaining > 0:
        notes.append("Available accounts could not fully cover spending need.")
    return DecumulationResult(withdrawals=withdrawals, notes=notes, unmet_need=round(remaining, 2))
