"""Fixed-order fallback and incremental tax-aware decumulation."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.calculators.marginal_cost import calculate_marginal_withdrawal_cost
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.parameters.loader import ResolvedParams


LEGACY_ORDER = ["taxable", "rrsp", "tfsa", "fhsa", "hisa", "rrif"]
LIQUID_FIRST_ORDER = ["hisa", "taxable"]
REGISTERED_ORDER = ["rrsp", "rrif"]
TAX_FREE_ORDER = ["tfsa", "fhsa"]
INCREMENTAL_WITHDRAWAL_STEP = 1000.0

# Planning policy, not a CRA constant. It balances current-year tax/benefit
# cost against preserving tax-free assets and must be revisited with household data.
REGISTERED_MARGINAL_COST_THRESHOLD = 0.35


@dataclass(frozen=True)
class DecumulationResult:
    withdrawals: dict[str, float]
    notes: list[str]
    unmet_need: float


def _withdraw_in_order(
    spending_need: float,
    accounts: list[InvestmentAccount],
    order: list[str],
) -> DecumulationResult:
    remaining = max(spending_need, 0.0)
    withdrawals: dict[str, float] = {}
    notes: list[str] = []
    accounts_by_type = sorted(accounts, key=lambda acct: order.index(acct.account_type.lower()) if acct.account_type.lower() in order else 99)
    for account in accounts_by_type:
        if remaining <= 0:
            break
        amount = min(account.current_balance, remaining)
        if amount <= 0:
            continue
        account.current_balance = max(account.current_balance - amount, 0.0)
        withdrawals[account.account_type] = withdrawals.get(account.account_type, 0.0) + round(amount, 2)
        remaining -= amount
        notes.append(f"Withdrew {amount:.2f} from {account.account_type}.")
    if remaining > 0:
        notes.append("Available accounts could not fully cover spending need.")
    return DecumulationResult(withdrawals=withdrawals, notes=notes, unmet_need=round(remaining, 2))


def _first_funded_account(
    accounts: list[InvestmentAccount],
    preferred_types: list[str],
) -> InvestmentAccount | None:
    for account_type in preferred_types:
        account = next(
            (
                candidate
                for candidate in accounts
                if candidate.account_type.lower() == account_type
                and candidate.current_balance > 0
            ),
            None,
        )
        if account is not None:
            return account
    return None


def _incremental_tax_aware_withdrawals(
    spending_need: float,
    accounts: list[InvestmentAccount],
    *,
    baseline_taxable_income: float,
    baseline_gis_income: float,
    earned_income: float,
    is_gis_eligible: bool,
    is_couple: bool,
    oas_received: float,
    resolved_params: ResolvedParams,
) -> DecumulationResult:
    remaining = max(spending_need, 0.0)
    withdrawals: dict[str, float] = {}
    notes = [
        "Using incremental tax-aware withdrawals; cash and taxable balances are used before registered or tax-free accounts."
    ]

    for account_type in LIQUID_FIRST_ORDER:
        for account in accounts:
            if remaining <= 0:
                break
            if account.account_type.lower() != account_type or account.current_balance <= 0:
                continue
            amount = min(account.current_balance, remaining)
            account.current_balance = max(account.current_balance - amount, 0.0)
            withdrawals[account.account_type] = withdrawals.get(account.account_type, 0.0) + amount
            remaining -= amount

    taxable_increment = 0.0
    last_strategy: str | None = None
    while remaining > 0:
        increment = min(INCREMENTAL_WITHDRAWAL_STEP, remaining)
        cost = calculate_marginal_withdrawal_cost(
            baseline_taxable_income + taxable_increment,
            baseline_gis_income=baseline_gis_income + taxable_increment,
            earned_income=earned_income,
            is_gis_eligible=is_gis_eligible,
            is_couple=is_couple,
            oas_received=oas_received,
            resolved=resolved_params,
            test_increment=increment,
        )
        prefer_registered = cost.effective_rate <= REGISTERED_MARGINAL_COST_THRESHOLD
        preferred_types = (
            [*REGISTERED_ORDER, *TAX_FREE_ORDER]
            if prefer_registered
            else [*TAX_FREE_ORDER, *REGISTERED_ORDER]
        )
        account = _first_funded_account(accounts, preferred_types)
        if account is None:
            account = next((candidate for candidate in accounts if candidate.current_balance > 0), None)
        if account is None:
            break

        strategy = "registered" if account.account_type.lower() in REGISTERED_ORDER else "tax-free"
        if strategy != last_strategy:
            notes.append(
                f"At taxable income ${baseline_taxable_income + taxable_increment:,.2f}, "
                f"registered marginal cost is {cost.effective_rate:.1%} "
                f"(tax ${cost.tax_component:,.2f}, OAS recovery ${cost.oas_recovery_component:,.2f}, "
                f"GIS loss ${cost.gis_component:,.2f}); preferring {strategy} funds."
            )
            last_strategy = strategy

        amount = min(account.current_balance, increment)
        account.current_balance = max(account.current_balance - amount, 0.0)
        withdrawals[account.account_type] = withdrawals.get(account.account_type, 0.0) + amount
        remaining -= amount
        if account.account_type.lower() in REGISTERED_ORDER:
            taxable_increment += amount

    for account_type, amount in withdrawals.items():
        notes.append(f"Withdrew {amount:.2f} from {account_type}.")
    if remaining > 0:
        notes.append("Available accounts could not fully cover spending need.")
    return DecumulationResult(
        withdrawals={key: round(value, 2) for key, value in withdrawals.items()},
        notes=notes,
        unmet_need=round(remaining, 2),
    )


def sequence_withdrawals(
    spending_need: float,
    accounts: list[InvestmentAccount],
    *,
    baseline_taxable_income: float | None = None,
    baseline_gis_income: float | None = None,
    earned_income: float = 0.0,
    is_gis_eligible: bool = False,
    is_couple: bool = False,
    oas_received: float = 0.0,
    resolved_params: ResolvedParams | None = None,
) -> DecumulationResult:
    """Withdraw funds incrementally when tax context is supplied.

    Callers without both taxable-income context and resolved parameters use the
    documented legacy order for backward compatibility. Tax-aware callers use
    liquid balances first, then re-evaluate registered versus tax-free funds at
    every increment using the planning threshold defined in this module.
    """

    if baseline_taxable_income is None or resolved_params is None:
        return _withdraw_in_order(spending_need, accounts, LEGACY_ORDER)
    return _incremental_tax_aware_withdrawals(
        spending_need,
        accounts,
        baseline_taxable_income=baseline_taxable_income,
        baseline_gis_income=(
            baseline_taxable_income
            if baseline_gis_income is None
            else baseline_gis_income
        ),
        earned_income=earned_income,
        is_gis_eligible=is_gis_eligible,
        is_couple=is_couple,
        oas_received=oas_received,
        resolved_params=resolved_params,
    )
