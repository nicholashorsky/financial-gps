# FIRE Engine Hardening — Build-State Engineering Spec
**Methodology:** `vibe_coding_prompt.md` (this document is pure **Build State** — no new product decisions, just the engineering breakdown for gaps #1–#3 flagged in `financial_gps_status_assessment.md`)
**Scope:** (1) RRIF conversion + minimum withdrawals, (2) marginal-rate-aware decumulation, (3) multi-year CRA parameter loading
**Non-goals:** province expansion, ACB/capital-gains tracking, pension splitting, Monte Carlo — all correctly deferred per the unified spec's roadmap
**Compatibility constraint:** every change below must keep the existing test suite green (`test_decumulation.py`, `test_projection.py`, `test_rrsp_room.py`, `smoke_test.py`) without modification unless explicitly noted

---

## 0. Why these three, and in this order

1. **RRIF conversion** is a correctness bug hiding behind a passing test suite — `evaluate_rules()` fires a string, but nothing downstream changes account behavior. Build this first because feature 2 (decumulation) needs RRIF-aware accounts to reason about correctly.
2. **Marginal-rate-aware decumulation** is the single feature the research report (`firecanadianresearchreport.md`) identifies as most likely to silently produce a *wrong* "optimal" withdrawal order for GIS-eligible or OAS-recovery-zone households. Build this second, on top of RRIF-aware accounts.
3. **Multi-year parameter loader** is lower risk but blocks anything that runs a projection across a year boundary correctly, and blocks Phase 8 beta users from trusting out-of-2026 dates. Build last — it's independent of 1 and 2.

---

## 1. Feature: RRIF Conversion & Minimum Withdrawals

### 1.1 Problem
`fire_engine/engine/rules.py::evaluate_rules` appends `"RRSP age-71 approaching"` to `triggered_rules`, but `fire_engine/engine/projection.py` never mutates the account or forces a withdrawal. An RRSP in the model can carry a balance forever past age 71, which is not legal and not representative of real cash flow.

### 1.2 CRA rule being modeled
- An RRSP must be converted (to a RRIF, an annuity, or cashed out) by **December 31 of the year the holder turns 71**.
- Starting the **year following conversion**, a **minimum withdrawal** is mandatory, taxable, and calculated as a prescribed percentage of the RRIF's fair market value at the start of that year.
- Prescribed factor = `1 / (90 - age)` for ages under 71 (early/voluntary RRIF); a fixed CRA table for ages 71+.

> ⚠️ **Verification flag:** the age-71+ factor table below reflects the standard post-2015 CRA prescribed factors used broadly in Canadian retirement tooling. Re-verify against the current CRA RC4178 / Income Tax Regulations Schedule III before this is used for real financial decisions — same caveat already applied to the OAS/GIS constants in `cra_2026.py`.

| Age | Factor | Age | Factor | Age | Factor |
|---|---|---|---|---|---|
| 71 | 5.28% | 79 | 6.58% | 87 | 9.55% |
| 72 | 5.40% | 80 | 6.82% | 88 | 10.21% |
| 73 | 5.53% | 81 | 7.08% | 89 | 10.99% |
| 74 | 5.67% | 82 | 7.38% | 90 | 11.92% |
| 75 | 5.82% | 83 | 7.71% | 91 | 13.06% |
| 76 | 5.98% | 84 | 8.08% | 92 | 14.49% |
| 77 | 6.17% | 85 | 8.51% | 93 | 16.34% |
| 78 | 6.36% | 86 | 8.99% | 94 | 18.79% |
| 95+ | 20.00% | | | | |

### 1.3 Data model changes

**`fire_engine/models/investment_account.py`** — add two fields:
```python
@dataclass
class InvestmentAccount:
    account_type: str
    current_balance: float
    opened_date: date | None = None
    institution: str | None = None
    beneficiary_type: str | None = None
    annual_return: float = 0.05
    rrif_conversion_year: int | None = None   # NEW — set once, on conversion
    is_rrif_minimum_tracked: bool = False     # NEW — true once conversion has happened

    def grow_one_year(self) -> None:
        self.current_balance *= 1 + self.annual_return
```

**`shared/db.py`** — add a column to `fire_investment_accounts` (nullable, additive migration only):
```sql
CREATE TABLE IF NOT EXISTS fire_investment_accounts (
    ...
    rrif_conversion_year   INTEGER
);
```
Add via `_ensure_column(db, "fire_investment_accounts", "rrif_conversion_year", "INTEGER")` in `init_db()`, following the existing additive-migration pattern already used for `accounts.account_key` etc.

**`fire_engine/models/tax_result.py`** — no change needed.

**`fire_engine/engine/projection.py` — `ProjectionYear`** — add one field for explainability:
```python
@dataclass(frozen=True)
class ProjectionYear:
    ...
    rrif_minimum_withdrawal: float   # NEW
```

### 1.4 New calculator: `fire_engine/calculators/rrif_minimum.py`

```python
"""RRIF conversion and prescribed minimum withdrawal calculator."""

from __future__ import annotations

from dataclasses import dataclass

RRIF_CONVERSION_AGE = 71          # must convert by Dec 31 of the year turning 71
RRIF_MINIMUM_START_AGE = 72       # first mandatory minimum-withdrawal year

# CRA prescribed factors, ages 71-94; age 95+ is flat 20%.
# Verify against current CRA RC4178 before production use.
RRIF_PRESCRIBED_FACTORS: dict[int, float] = {
    71: 0.0528, 72: 0.0540, 73: 0.0553, 74: 0.0567, 75: 0.0582,
    76: 0.0598, 77: 0.0617, 78: 0.0636, 79: 0.0658, 80: 0.0682,
    81: 0.0708, 82: 0.0738, 83: 0.0771, 84: 0.0808, 85: 0.0851,
    86: 0.0899, 87: 0.0955, 88: 0.1021, 89: 0.1099, 90: 0.1192,
    91: 0.1306, 92: 0.1449, 93: 0.1634, 94: 0.1879,
}
RRIF_FACTOR_95_PLUS = 0.20


@dataclass(frozen=True)
class RRIFMinimumResult:
    age: int
    factor: float
    minimum_withdrawal: float


def rrif_prescribed_factor(age: int) -> float:
    if age < RRIF_CONVERSION_AGE:
        return round(1 / (90 - age), 4)
    if age >= 95:
        return RRIF_FACTOR_95_PLUS
    return RRIF_PRESCRIBED_FACTORS.get(age, RRIF_FACTOR_95_PLUS)


def calculate_rrif_minimum(age: int, fair_market_value_jan1: float) -> RRIFMinimumResult:
    """Minimum withdrawal for the year, given age and Jan-1 fair market value.

    No minimum applies in the conversion year itself or earlier — callers should
    only invoke this once age >= RRIF_MINIMUM_START_AGE.
    """
    factor = rrif_prescribed_factor(age)
    minimum = round(max(fair_market_value_jan1, 0.0) * factor, 2)
    return RRIFMinimumResult(age=age, factor=factor, minimum_withdrawal=minimum)
```

Export it from `fire_engine/calculators/__init__.py` alongside the existing calculators.

### 1.5 Engine changes: `fire_engine/engine/projection.py`

Insert conversion + minimum-withdrawal logic **before** the existing tax/spending block, using the Jan-1 balance (i.e., balance *before* growth is applied for that year):

```python
from fire_engine.calculators.rrif_minimum import (
    RRIF_CONVERSION_AGE,
    RRIF_MINIMUM_START_AGE,
    calculate_rrif_minimum,
)

# ... inside the yearly loop, after `age = household.primary.age_in_year(year)`:

rrif_minimum_withdrawal = 0.0
for account in accounts:
    if account.account_type.lower() == "rrsp" and age >= RRIF_CONVERSION_AGE:
        account.account_type = "rrif"
        account.rrif_conversion_year = year

    if account.account_type.lower() == "rrif" and age >= RRIF_MINIMUM_START_AGE:
        result = calculate_rrif_minimum(age, account.current_balance)
        withdrawal = min(result.minimum_withdrawal, account.current_balance)
        account.current_balance -= withdrawal
        rrif_minimum_withdrawal += withdrawal

# Fold the mandatory withdrawal into taxable income alongside CPP/OAS:
pretax_income = employment_income + cpp_received + oas_received + rrif_minimum_withdrawal
```

`ProjectionYear(...)` construction gains `rrif_minimum_withdrawal=round(rrif_minimum_withdrawal, 2)`.

### 1.6 Rules registry: `fire_engine/engine/rules.py`

Keep the existing early-warning rule, and add two new ones that reflect actual state changes (not just proximity):

```python
def evaluate_rules(year: int, household: Household, projected_income: float) -> list[str]:
    rules: list[str] = []
    age = household.primary.age_in_year(year)
    if age >= 69 and age <= 70:
        rules.append("RRSP age-71 approaching")
    if age == 71:
        rules.append("RRSP converted to RRIF this year")
    if age >= 72:
        rules.append("RRIF minimum withdrawal in effect")
    if projected_income >= 80323:
        rules.append("OAS threshold proximity")
    if household.primary.is_quebec:
        rules.append("Quebec support coming soon")
    return rules
```
(Adjust the `69–70` window since `71` and `72+` now have their own explicit rules — avoids redundant overlapping strings.)

### 1.7 Service layer / UI touch points
- `shared/fire_service.py::build_household` — no change required; `InvestmentAccount(**row)` already forwards unknown-to-it kwargs only if explicitly listed, so **add** `rrif_conversion_year` to the constructor call once the DB column exists.
- `pages/fire_forecast.py` — add an "RRIF minimum" column to the year-by-year drillable table (`frame` DataFrame), sourced from `year.rrif_minimum_withdrawal`.
- `pages/data_quality.py` — no change; existing `rrsp_age_71` warning in `shared/fire_service.py::get_data_quality_warnings` still fires correctly as an early heads-up and doesn't need to know about the mechanical conversion.

### 1.8 Test plan
New file `tests/calculators/test_rrif_minimum.py`:
- `rrif_prescribed_factor(71) == 0.0528`, `rrif_prescribed_factor(95) == 0.20`, `rrif_prescribed_factor(60) == round(1/30, 4)`.
- `calculate_rrif_minimum(72, 100000).minimum_withdrawal == 5400.0`.

Extend `tests/engine/test_projection.py`:
- New fixture `tests/fixtures/household_near_rrif.json`: primary born so they turn 71 in year 3 of a 10-year projection, RRSP balance 200,000, no other income.
- Assert: year 3 → account_type becomes `"rrif"`; year 4 → `rrif_minimum_withdrawal > 0` and matches `calculate_rrif_minimum(72, balance_at_start_of_year4)`; year 2 → `rrif_minimum_withdrawal == 0`.

---

## 2. Feature: Marginal-Rate-Aware Decumulation Sequencer

### 2.1 Problem
`fire_engine/calculators/decumulation.py::sequence_withdrawals` withdraws in a **fixed order** (`taxable → rrsp → tfsa → fhsa → hisa → rrif`) regardless of tax bracket, OAS recovery zone, or GIS eligibility. The file's own docstring and the unified spec's folder-structure comment both claim this is "marginal-rate-aware" — it isn't yet.

### 2.2 Design principle
Rather than hardcoding new GIS/OAS thresholds a second time, **reuse the existing tested calculators** (`calculate_federal_tax`, `calculate_ontario_tax`, `estimate_gis`) via a **finite-difference marginal-cost estimate**: bump taxable income by a small test increment, see how much extra tax + lost GIS + OAS recovery tax that increment causes, and divide by the increment to get an effective marginal rate. This avoids duplicating threshold logic and stays correct automatically if those calculators change.

### 2.3 New calculator: `fire_engine/calculators/marginal_cost.py`

```python
"""Marginal cost of one additional dollar of taxable withdrawal income.

Used by the decumulation sequencer to decide whether pulling from a
registered (taxable-on-withdrawal) account is cheaper than pulling from a
tax-free account this year.
"""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.calculators.gis_estimator import estimate_gis
from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
from fire_engine.parameters.loader import ResolvedParams, get_params

DEFAULT_TEST_INCREMENT = 1000.0


@dataclass(frozen=True)
class MarginalCostResult:
    baseline_income: float
    effective_rate: float          # 0.0-1.0+, combined tax + OAS recovery + GIS loss
    tax_component: float
    oas_recovery_component: float
    gis_component: float


def calculate_marginal_withdrawal_cost(
    baseline_taxable_income: float,
    is_gis_eligible: bool = False,
    is_couple: bool = False,
    resolved: ResolvedParams | None = None,
    test_increment: float = DEFAULT_TEST_INCREMENT,
) -> MarginalCostResult:
    resolved = resolved or get_params(2026, "ON")
    params = resolved.params

    base_fed = calculate_federal_tax(baseline_taxable_income, resolved).federal_tax
    base_prov = calculate_ontario_tax(baseline_taxable_income, resolved).provincial_tax
    bumped_income = baseline_taxable_income + test_increment
    bumped_fed = calculate_federal_tax(bumped_income, resolved).federal_tax
    bumped_prov = calculate_ontario_tax(bumped_income, resolved).provincial_tax
    tax_component = (bumped_fed - base_fed) + (bumped_prov - base_prov)

    oas_recovery_component = 0.0
    threshold = params.oas_recovery_threshold
    if bumped_income > threshold:
        excess_base = max(baseline_taxable_income - threshold, 0.0)
        excess_bumped = max(bumped_income - threshold, 0.0)
        oas_recovery_component = (excess_bumped - excess_base) * 0.15

    gis_component = 0.0
    if is_gis_eligible:
        gis_before = estimate_gis(baseline_taxable_income, 0.0, is_couple, resolved).annual_amount
        gis_after = estimate_gis(bumped_income, 0.0, is_couple, resolved).annual_amount
        gis_component = max(gis_before - gis_after, 0.0)

    total_cost = tax_component + oas_recovery_component + gis_component
    effective_rate = round(total_cost / test_increment, 4)
    return MarginalCostResult(
        baseline_income=baseline_taxable_income,
        effective_rate=effective_rate,
        tax_component=round(tax_component, 2),
        oas_recovery_component=round(oas_recovery_component, 2),
        gis_component=round(gis_component, 2),
    )
```

Export from `fire_engine/calculators/__init__.py`.

### 2.4 Updated sequencer: `fire_engine/calculators/decumulation.py`

Keep the existing function signature working (backward-compatible default path) and add an optional tax-aware path:

```python
"""Decumulation sequencer — fixed-order fallback, or marginal-rate-aware when
tax context is supplied."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.calculators.marginal_cost import calculate_marginal_withdrawal_cost
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.parameters.loader import ResolvedParams

REGISTERED_MARGINAL_COST_THRESHOLD = 0.30  # tune via test fixtures, not a CRA constant

TAX_FREE_FIRST_ORDER = ["hisa", "taxable", "tfsa", "rrsp", "rrif", "fhsa"]
REGISTERED_FIRST_ORDER = ["hisa", "taxable", "rrsp", "rrif", "tfsa", "fhsa"]
LEGACY_ORDER = ["taxable", "rrsp", "tfsa", "fhsa", "hisa", "rrif"]


@dataclass(frozen=True)
class DecumulationResult:
    withdrawals: dict[str, float]
    notes: list[str]
    unmet_need: float


def _withdraw_in_order(spending_need: float, accounts: list[InvestmentAccount], order: list[str]) -> DecumulationResult:
    remaining = max(spending_need, 0.0)
    withdrawals: dict[str, float] = {}
    notes: list[str] = []
    accounts_by_type = sorted(
        accounts,
        key=lambda acct: order.index(acct.account_type.lower()) if acct.account_type.lower() in order else 99,
    )
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


def sequence_withdrawals(
    spending_need: float,
    accounts: list[InvestmentAccount],
    *,
    baseline_taxable_income: float | None = None,
    is_gis_eligible: bool = False,
    is_couple: bool = False,
    resolved_params: ResolvedParams | None = None,
) -> DecumulationResult:
    """Withdraw to cover spending_need.

    Legacy behavior (unchanged) when no tax context is supplied — keeps existing
    callers and tests working. When `baseline_taxable_income` is supplied, compares
    the marginal cost of tapping registered accounts vs. TFSA and picks an order
    accordingly, logging the reasoning in `notes`.
    """
    if baseline_taxable_income is None:
        return _withdraw_in_order(spending_need, accounts, LEGACY_ORDER)

    cost = calculate_marginal_withdrawal_cost(
        baseline_taxable_income,
        is_gis_eligible=is_gis_eligible,
        is_couple=is_couple,
        resolved=resolved_params,
    )
    order = TAX_FREE_FIRST_ORDER if cost.effective_rate > REGISTERED_MARGINAL_COST_THRESHOLD else REGISTERED_FIRST_ORDER
    result = _withdraw_in_order(spending_need, accounts, order)
    reason = (
        f"RRSP/RRIF marginal cost {cost.effective_rate:.0%} "
        f"(tax {cost.tax_component:.2f}, OAS recovery {cost.oas_recovery_component:.2f}, "
        f"GIS loss {cost.gis_component:.2f}) — "
        + ("preferring TFSA over RRSP/RRIF." if order is TAX_FREE_FIRST_ORDER else "preferring RRSP/RRIF over TFSA.")
    )
    return DecumulationResult(withdrawals=result.withdrawals, notes=[reason, *result.notes], unmet_need=result.unmet_need)
```

**Note:** `REGISTERED_MARGINAL_COST_THRESHOLD = 0.30` is an engineering tuning constant, not a CRA figure — flag it as such in code comments so nobody mistakes it for an official value. Revisit once real households are tested against it.

### 2.5 Engine integration: `fire_engine/engine/projection.py`

Replace the existing call site:
```python
if net_surplus < 0:
    decumulation = sequence_withdrawals(
        abs(net_surplus),
        accounts,
        baseline_taxable_income=pretax_income,
        is_gis_eligible=gis_received > 0,
        is_couple=False,          # single-household MVP; revisit when couples are modeled
        resolved_params=get_params(year, household.primary.province),
    )
    sequencer_notes = decumulation.notes
    net_surplus = -decumulation.unmet_need
```
(`get_params` import already exists transitively via calculators — add a direct import in `projection.py` if not already present.)

### 2.6 Test plan
New file `tests/calculators/test_marginal_cost.py`:
- Low income (e.g., $20,000 baseline, `is_gis_eligible=True`) → `effective_rate` should reflect the GIS clawback component being non-zero and dominant.
- Income just under the OAS recovery threshold, bumped over it → `oas_recovery_component > 0`.
- Comfortable middle income (e.g., $60,000, not GIS-eligible, well under OAS threshold) → `effective_rate` roughly equals the marginal tax bracket rate only.

Extend `tests/calculators/test_decumulation.py`:
- Existing test (`test_taxable_then_rrsp_then_tfsa_order`) must still pass unmodified — confirms backward compatibility.
- New test: GIS-eligible low-income household with both TFSA and RRSP balances and a spending need → assert TFSA is drawn down before RRSP (`REGISTERED_FIRST_ORDER` not chosen).
- New test: comfortable middle-income household → assert RRSP is drawn down before TFSA (`TAX_FREE_FIRST_ORDER` not chosen).

Extend `tests/engine/test_projection.py`:
- Reuse `household_couple_gis_eligible.json` fixture (already exists) — assert `sequencer_notes` in at least one shortfall year mentions "GIS loss" and prefers TFSA.

---

## 3. Feature: Multi-Year Parameter Loader

### 3.1 Problem
`fire_engine/parameters/loader.py::get_params` silently returns 2026 parameters for any year not equal to 2026:
```python
if year != 2026:
    # Future: load cra_2024.py, cra_2025.py as needed
    pass
```
This is dangerous: a caller passing `2025` (a real, plausible year given `RRSPRoomResult.snapshot_year` and similar fields) gets 2026 numbers with no warning.

### 3.2 Design: registry + explicit failure, not fabricated historical data
This spec does **not** attempt to source exact historical 2024/2025 CRA figures (risk of silently-wrong financial numbers is worse than an explicit error). Instead:

**New exception — `fire_engine/parameters/errors.py`:**
```python
"""Parameter-loading errors."""

from __future__ import annotations


class UnsupportedTaxYearError(ValueError):
    """Raised when CRA parameters for the requested year have not been loaded."""

    def __init__(self, year: int, supported_years: list[int]):
        self.year = year
        self.supported_years = supported_years
        super().__init__(
            f"No CRA parameters loaded for {year}. Supported years: {sorted(supported_years)}. "
            f"Add fire_engine/parameters/cra_{year}.py and register it in loader.YEAR_PARAMS_REGISTRY."
        )
```

**Updated `fire_engine/parameters/loader.py`:**
```python
from fire_engine.parameters.cra_2026 import CRA2026Params, CRA_2026
from fire_engine.parameters.errors import UnsupportedTaxYearError

YEAR_PARAMS_REGISTRY: dict[int, CRA2026Params] = {
    2026: CRA_2026,
}

def get_params(
    year: int = 2026,
    province: str = "ON",
    effective_date: date | None = None,
) -> ResolvedParams:
    eff = effective_date or date(year, 7, 1)

    if province == "QC":
        raise ValueError("Quebec support coming soon.")

    if year not in YEAR_PARAMS_REGISTRY:
        raise UnsupportedTaxYearError(year, list(YEAR_PARAMS_REGISTRY.keys()))

    base = YEAR_PARAMS_REGISTRY[year]
    quarter = _quarter_from_date(eff)
    index_factor = OAS_QUARTERLY_INDEX.get((year, quarter), 1.0)
    if index_factor != 1.0:
        adjusted = CRA2026Params(
            oas_max_monthly_65_74=base.oas_max_monthly_65_74 * index_factor,
            oas_max_monthly_75_plus=base.oas_max_monthly_75_plus * index_factor,
        )
        return ResolvedParams(year=year, province=province, effective_date=eff, params=adjusted)
    return ResolvedParams(year=year, province=province, effective_date=eff, params=base)
```

### 3.3 Runbook: adding a new tax year (e.g., 2027)
1. Copy `fire_engine/parameters/cra_2026.py` → `fire_engine/parameters/cra_2027.py`, rename the dataclass/constant (`CRA2027Params` / `CRA_2027`).
2. Pull the new year's values from the current CRA T4032 (federal + Ontario) and update every field — brackets, BPA, TFSA/RRSP limits, CPP/OAS/GIS thresholds, regression test cases.
3. Register it: `YEAR_PARAMS_REGISTRY[2027] = CRA_2027` in `loader.py`.
4. Add `tests/calculators/test_federal_tax_2027.py` / `test_provincial_tax_on_2027.py` with that year's official CRA regression cases (mirrors the existing 2026 gate pattern).
5. Update `OAS_QUARTERLY_INDEX` with the new year's quarterly indexation once published.

### 3.4 Call-site audit
Search for every caller passing a non-default `year`/`snapshot_year` to `get_params` and confirm each either (a) always passes 2026 today, or (b) needs a `try/except UnsupportedTaxYearError` with a user-facing message. Known call sites to check:
- `fire_engine/calculators/rrsp_room.py::calculate_rrsp_room` — calls `get_params(snapshot_year, "ON")` where `snapshot_year` comes from user input (`fire_room_tracker.py`). **Needs a guard** — wrap in the UI layer (`pages/fire_room_tracker.py`) to show `st.error(str(exc))` instead of crashing the page.
- `fire_engine/calculators/tfsa_room.py`, `fhsa_state.py` — same pattern, same guard needed.
- `fire_engine/engine/projection.py` — now calls `get_params(year, ...)` per-year (see §2.5) across a 40-year loop that will **always** hit years beyond 2026. **This is the most important call site to fix** — see §3.5.

### 3.5 Consequence for the 40-year projection loop
Because `project_household` runs 40 years forward from `start_year` (2026), most of those years will raise `UnsupportedTaxYearError` under a strict registry until historical/future-year modules exist. Two acceptable interim strategies (pick one, document the choice in code):

- **Option A (recommended for now):** keep using 2026 params for all projection years, but do it **explicitly and visibly** rather than silently:
  ```python
  try:
      resolved = get_params(year, household.primary.province)
  except UnsupportedTaxYearError:
      resolved = get_params(2026, household.primary.province)
      # explicit, logged assumption — not a silent fallback
  ```
  Surface this as a standing note in the Data Quality Panel: *"Tax parameters beyond 2026 are assumed flat at 2026 levels until future-year CRA data is loaded."*
- **Option B:** raise immediately and require real yearly parameter modules before any multi-year projection can run. Safer, but blocks the FIRE Forecast page entirely until real historical/projected brackets exist for ~40 years — not realistic short-term.

**Recommendation: Option A**, implemented as a named helper `get_params_or_2026_fallback(year, province)` in `loader.py` so the "flat assumption" is a single, greppable, documented choice rather than scattered try/excepts.

### 3.6 Test plan
New file `tests/parameters/test_loader.py`:
- `get_params(2026, "ON")` still works exactly as before (regression).
- `get_params(2025, "ON")` raises `UnsupportedTaxYearError`.
- `get_params_or_2026_fallback(2031, "ON")` returns 2026 params without raising.
- `UnsupportedTaxYearError.supported_years == [2026]` today.

---

## 4. File/Folder Diff Summary

```
fire_engine/
├── calculators/
│   ├── rrif_minimum.py          NEW
│   ├── marginal_cost.py         NEW
│   ├── decumulation.py          MODIFIED (backward-compatible signature change)
│   └── __init__.py              MODIFIED (export new calculators)
├── engine/
│   ├── projection.py            MODIFIED (RRIF logic + tax-aware sequencer call)
│   └── rules.py                 MODIFIED (RRIF-state-aware rule strings)
├── models/
│   └── investment_account.py    MODIFIED (+rrif_conversion_year, +is_rrif_minimum_tracked)
└── parameters/
    ├── errors.py                 NEW
    └── loader.py                 MODIFIED (registry pattern + explicit errors + fallback helper)

shared/
├── db.py                         MODIFIED (+rrif_conversion_year column, additive migration)
└── fire_service.py                MODIFIED (pass rrif_conversion_year through build_household)

pages/
├── fire_forecast.py              MODIFIED (+RRIF minimum column in drillable table)
└── fire_room_tracker.py          MODIFIED (+guard UnsupportedTaxYearError with st.error)

tests/
├── calculators/
│   ├── test_rrif_minimum.py      NEW
│   ├── test_marginal_cost.py     NEW
│   └── test_decumulation.py      MODIFIED (add GIS/OAS-aware ordering cases)
├── engine/
│   └── test_projection.py        MODIFIED (add household_near_rrif.json coverage)
├── parameters/
│   └── test_loader.py            NEW
└── fixtures/
    └── household_near_rrif.json  NEW
```

---

## 5. Implementation Order (small, sequential, testable steps)

1. `rrif_minimum.py` + its unit tests — pure function, zero blast radius.
2. `investment_account.py` model fields + `shared/db.py` column + `fire_service.py` passthrough.
3. `projection.py` RRIF conversion/withdrawal logic + `rules.py` rule updates + new fixture + projection test.
4. `marginal_cost.py` + its unit tests — pure function, zero blast radius.
5. `decumulation.py` signature extension (verify legacy test still passes untouched) + new ordering tests.
6. Wire `projection.py` to call the tax-aware `sequence_withdrawals` path + extend projection test for sequencer notes.
7. `parameters/errors.py` + `loader.py` registry refactor + `test_loader.py`.
8. Guard the three room-tracker call sites (`rrsp_room.py`, `tfsa_room.py`, `fhsa_state.py` callers in `fire_room_tracker.py`) against `UnsupportedTaxYearError`.
9. UI polish: RRIF column in `fire_forecast.py`, Data Quality Panel note about the 2026-flat-assumption fallback.
10. Full regression pass: `tests/smoke_test.py` + entire suite green before merge.

---

## 6. Out-of-Scope Notes (flagged, not specced here)

- **`fire_projection_years` table is never written to.** `project_user_household` returns in-memory `ProjectionYear` objects only; nothing persists them to the SQL table that already exists in the schema. Worth a follow-up spec if audit-trail/history-across-sessions is wanted (the research report's "audit-grade assumption versioning" theme).
- **`is_couple` is hardcoded `False`** in the projection's call to the tax-aware sequencer — correct for the current single-household MVP, but will need real plumbing once couples/pension-splitting (V2 per the unified spec) land.
- **Real historical CRA figures for 2024/2025** are intentionally not fabricated in this spec — populate `cra_2024.py`/`cra_2025.py` from verified CRA T4032 archives when that becomes a real product need.

---

*This spec is ready to hand to a coding session file-by-file, in the order listed in §5. Each step has an isolated blast radius and its own test, so a partial implementation still leaves the app in a working state.*
