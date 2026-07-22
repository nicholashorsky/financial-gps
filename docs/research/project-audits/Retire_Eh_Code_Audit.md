# Retire, Eh? — Code Audit

**Repository:** `halfguru/retire-eh`  
**Audit date:** 2026-07-22  
**Default branch:** `main`  
**License:** MIT  
**Audit purpose:** Evaluate Retire, Eh? as a reusable or reference foundation for a Canadian, ProjectionLab-inspired personal financial-planning application.

---

## 1. Executive Assessment

Retire, Eh? is a small, clearly structured Canadian retirement accumulation calculator. Its strongest qualities are:

- Canadian terminology and account wrappers
- A compact Rust calculation core compiled to WebAssembly
- Browser-local execution
- Straightforward React architecture
- Transparent formulas
- MIT licensing
- Automated frontend and backend tests
- YAML import/export and local persistence

However, the current codebase is much less sophisticated than its product description may initially suggest. The audited Rust engine primarily:

- Grows RRSP, TFSA, RESP, and non-registered balances using one shared fixed return rate
- Adds fixed monthly contributions
- Projects only until retirement
- Uses a fixed 4% withdrawal estimate at retirement
- Does not model retirement-year withdrawals
- Does not calculate Canadian income tax
- Does not calculate CPP or OAS benefits in the audited core
- Does not model TFSA room, RRSP room, RRIF conversions, capital gains, dividends, or tax-aware drawdown
- Does not implement Monte Carlo or historical backtesting

### Recommendation

Use Retire, Eh? as:

- A reference for a compact Rust/WASM calculation boundary
- A starting point for local-first architecture
- A source of simple accumulation formulas and tests
- A reference for household-first UI organization
- A potentially reusable frontend scaffold under MIT terms

Do **not** treat its existing calculation engine as a sufficient Canadian planning engine. It would require a substantial rewrite or expansion.

---

## 2. Repository Positioning

The README describes the product as:

- A household-first Canadian retirement planner
- Focused on RRSP, TFSA, and CPP strategy
- Conservative and transparent
- Fully browser-local
- Powered by Rust/WebAssembly

It explicitly excludes:

- Bank linking
- Real-time market data
- Complex tax optimization
- Monte Carlo simulations
- Non-Canadian retirement accounts

This positioning is broadly accurate regarding scope, but the present core is still at an early accumulation-calculator stage.

---

## 3. Technology Stack

### Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
- Recharts
- Zod
- js-yaml
- Vitest
- Testing Library

### Calculation core

- Rust
- `wasm-bindgen`
- `serde`
- `serde-wasm-bindgen`
- Compiled to WebAssembly

### Deployment and CI

- GitHub Pages deployment
- GitHub Actions
- Frontend type checking, linting, build, and tests
- Rust tests, Clippy, formatting checks, and WASM build

---

## 4. High-Level Architecture

The documented component structure is:

```text
App.tsx
├── PeopleProvider
│   └── AssumptionsProvider
│       └── ProjectionProvider
│           └── AppContent
│               ├── Header
│               ├── Tabs
│               ├── OverviewTab
│               ├── PlanTab
│               ├── ProjectionsTab
│               ├── IncomeTab
│               ├── LearnTab
│               └── Footer
├── Shell ErrorBoundary
└── Tab ErrorBoundary
```

### State ownership

- `PeopleProvider`: people CRUD and active-person selection
- `AssumptionsProvider`: assumptions and local-storage persistence
- `ProjectionProvider`: derived projection data
- `usePersistence`: local-storage coordination
- Leaf components consume contexts directly

### Navigation model

Five horizontal tabs:

1. Plan
2. Overview
3. Projections
4. Income
5. Learn

### Mobile behaviour

- Horizontally scrollable tabs
- Sticky tab bar
- Minimum 44px touch targets

---

## 5. Calculation Boundary

The Rust library exposes a `RetirementCalculator` class through WebAssembly.

Public methods:

```text
calculate_projection(...)
calculate_yearly_projections(...)
calculate_simple_projection(...)
calculate_additional_annual_savings(...)
```

The browser passes serialized JavaScript values into Rust. Rust deserializes them into typed models, performs calculations, and serializes results back to JavaScript.

### Positive architectural characteristics

- Financial formulas live in one language and module
- Rust functions are independently testable
- UI code does not need to reproduce financial formulas
- WebAssembly keeps calculations local
- Typed DTOs make the JS/Rust boundary explicit

### Risks

- Generated WASM bindings must remain synchronized
- Field naming can break at the boundary
- Rust model changes require coordinated frontend changes
- Debugging is more complex than an all-TypeScript implementation
- WebAssembly does not automatically improve speed for small annual simulations

For this project, the strongest reason to use Rust is determinism and isolation—not performance.

---

## 6. Audited Core Data Model

### HouseholdConfig

```text
retirement_age
expected_annual_income
```

`expected_annual_income` is present in the model but is not used by the audited projection functions.

### AccountBalance

```text
rrsp
tfsa
resp
non_registered
```

### ContributionConfig

```text
rrsp_annual
tfsa_annual
resp_annual
non_registered_annual
```

### ChildInfo

```text
age
target_contribution
```

The child array is accepted by `calculate_projection`, but the audited function ignores it.

### Assumptions

```text
return_rate
inflation_rate
```

Inflation is not used by the main retirement accumulation calculation. It is used only in the additional-savings calculation.

### RetirementProjection

```text
current_age
retirement_age
years_to_retirement
net_worth_at_retirement
annual_withdrawal
pension_equivalent
```

### YearlyProjection

```text
year
age
rrsp
tfsa
resp
non_registered
total_net_worth
```

---

## 7. Calculation Logic

## 7.1 Main retirement projection

The calculation:

1. Computes years until retirement.
2. Combines RRSP, TFSA, and non-registered balances.
3. Excludes RESP from the main retirement total.
4. Combines RRSP, TFSA, and non-registered contributions.
5. Converts annual return and contributions to monthly values.
6. Uses a future-value formula over the months to retirement.
7. Calculates annual withdrawal as 4% of retirement net worth.
8. Sets `pension_equivalent` equal to the same 4% amount.

### Formula behaviour

```text
monthly return = annual return / 100 / 12
monthly contribution = annual contributions / 12
future value = compounded opening balance + future value of monthly contributions
safe withdrawal = retirement portfolio × 4%
```

### Limitations

- No account-specific return assumptions
- No tax drag
- No contribution limits
- No deductions
- No employer matching
- No sequence-of-returns risk
- No retirement decumulation
- No spending model
- No life expectancy
- No benefit income
- No tax calculations
- No asset allocation
- No contribution timing choice
- RESP is ignored in the retirement summary

---

## 7.2 Yearly account projections

Each account is grown independently, but all accounts use the same monthly return rate.

For each month:

```text
new balance = old balance × (1 + monthly return) + monthly contribution
```

The function records one output per year from current age through retirement age.

### Strengths

- Simple
- Predictable
- Easy to validate
- Account balances remain separated in output

### Limitations

- Contributions are assumed at month-end after growth
- No withdrawals
- No taxes
- No fees
- No volatility
- No account room
- No transfers
- No rebalancing
- No cash account
- No ownership
- No spouse-specific account logic
- No retirement-period projection

---

## 7.3 Simple projection

The simple function compounds a single portfolio annually:

```text
portfolio value = opening portfolio × (1 + annual rate)^year
```

It does not include contributions.

If the user is already at retirement age, it returns an empty array rather than a one-point series.

---

## 7.4 Required additional savings

This function estimates the extra annual contribution needed to reach a target.

Process:

1. Convert annual return and inflation to monthly rates.
2. Inflate/deflate the simulated ending balance into real terms.
3. Use binary search for up to 100 iterations.
4. Stop when within $100 of the target.
5. Return additional annual contribution above current contributions.
6. Round to the nearest dollar.

### Positive aspects

- Handles zero-year and already-funded cases
- Uses a bounded numerical search
- Adjusts target comparison for inflation
- Avoids requiring a closed-form derivation

### Concerns

- Search upper bound is at least $1,000,000 annually
- Tolerance is fixed at $100
- Return and inflation are treated as smooth monthly rates
- No contribution limits or tax effects
- The calculation operates on one combined portfolio

---

## 8. Canadian Functionality Assessment

| Capability | Present in audited core | Notes |
|---|---:|---|
| RRSP balance | Yes | Wrapper only |
| TFSA balance | Yes | Wrapper only |
| RESP balance | Yes | Accumulation only |
| Non-registered balance | Yes | No tax treatment |
| CPP calculation | No | Product UI may mention CPP, but not in audited Rust models |
| OAS calculation | No | Not present in audited core |
| GIS calculation | No | Not present |
| Federal tax | No | Not present |
| Provincial tax | No | Not present |
| RRSP deduction | No | Not present |
| RRSP withdrawal tax | No | Not present |
| RRIF conversion | No | Not present |
| RRIF minimums | No | Not present |
| TFSA room | No | Not present |
| Capital gains | No | Not present |
| Dividend credits | No | Not present |
| OAS clawback | No | Not present |
| Spousal attribution | No | Not present |
| Estate modelling | No | Not present |
| CPP claiming adjustment | No | Not present |
| Historical simulation | No | Explicitly excluded |
| Monte Carlo | No | Explicitly excluded |

---

## 9. Testing

The project documentation reports:

### Frontend

Approximately 60 tests across:

- WASM bridge mapping
- People context CRUD and selection
- Import behaviour
- Zod validation
- YAML utilities
- WASM loader

### Backend

Approximately 19 Rust calculation tests in:

```text
backend/tests/calculations_test.rs
```

### Test architecture strengths

- Core formulas can be tested without rendering UI
- JS/WASM boundary has explicit tests
- Validation and import/export are tested
- CI runs both frontend and backend checks

### Recommended additions

- Golden-file projection tests
- Property-based tests
- Negative-return tests
- Large-value and small-value tests
- Contribution-timing tests
- Real-versus-nominal consistency tests
- Account-specific growth tests
- Canadian tax-year fixtures
- TFSA and RRSP room fixtures
- Retirement drawdown fixtures

---

## 10. Persistence and Privacy

The application is designed to run locally in the browser.

Documented capabilities include:

- LocalStorage persistence
- YAML import/export
- No bank linking
- No server required for calculations

### Advantages

- Strong privacy story
- Easy self-hosting
- Simple infrastructure
- No database migrations
- Easy offline or static hosting

### Tradeoffs

- Browser storage can be cleared
- Cross-device sync is absent
- Multi-user collaboration is absent
- Backup is user-managed
- Large simulation datasets may strain browser storage
- Schema migrations require careful client-side handling

For a personal project, local-first storage is a strong initial option.

---

## 11. License Audit

The repository is MIT licensed.

MIT generally permits:

- Use
- Copying
- Modification
- Distribution
- Sublicensing
- Commercial use

The copyright and permission notice must be retained in copies or substantial portions.

### Practical recommendation

Direct reuse is materially easier than with Ignidash. Still:

- Preserve the license notice
- Document copied or adapted files
- Avoid presenting original authorship as your own
- Confirm all bundled dependencies and assets have compatible licenses

This is not legal advice.

---

## 12. Reusability Matrix

| Area | Recommendation |
|---|---|
| Rust/WASM boundary | Reuse or adapt |
| Basic accumulation formulas | Reuse with tests |
| Additional-savings binary search | Adapt |
| React context layout | Reference or reuse |
| Local persistence | Reuse/adapt |
| YAML import/export | Reuse/adapt |
| Charts | Reference |
| Canadian tax engine | Replace |
| CPP/OAS engine | Build |
| Retirement drawdown | Build |
| Historical simulation | Build elsewhere |
| Monte Carlo | Build elsewhere |
| ProjectionLab-style plan events | Build |
| Ordered cash-flow flows | Build |
| Milestones | Build |
| Real assets and debts | Build |

---

## 13. Recommended Integration Strategy

### Best option

Use Retire, Eh? as a small reference implementation and selectively port:

- Rust/WASM interface pattern
- Validation patterns
- Local persistence
- Import/export
- Basic account accumulation tests
- Additional savings calculation

Then create a new domain model around:

```text
People
Accounts
Income events
Expense events
Flows
Milestones
Real assets
Debts
Tax assumptions
Simulation settings
Annual ledger outputs
```

### Avoid

Do not continually patch the current `HouseholdConfig` model into a ProjectionLab-like model. The current DTOs are too small. Create versioned domain objects instead.

---

## 14. Required Engine Expansion

A production-quality Canadian engine would need separate modules for:

```text
calendar
inflation
market returns
accounts
contribution room
income
expenses
payroll deductions
federal tax
provincial tax
CPP
OAS
GIS
RRSP
RRIF
TFSA
non-registered investments
capital gains
dividends
debts
real assets
withdrawal strategy
estate
historical simulation
Monte Carlo
```

The simulation should produce an annual ledger with explainable transactions, not only ending balances.

---

## 15. Final Verdict

### Overall score as a direct foundation: 4/10

### Overall score as a reference or reusable utility source: 7/10

Retire, Eh? is clean, approachable, and permissively licensed. Its architecture is useful, but its financial engine is currently an accumulation calculator rather than a complete Canadian retirement planner.

Its best contribution to the new project is:

> A compact, testable, local-first calculation architecture—not a finished Canadian projection engine.

---

## 16. Audited Primary Files

- `README.md`
- `AGENTS.md`
- `frontend/package.json`
- `backend/src/lib.rs`
- `backend/src/models.rs`
- `backend/src/calculations.rs`

Repository:  
https://github.com/halfguru/retire-eh
