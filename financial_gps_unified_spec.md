# Financial GPS — Unified Product Spec
## Spec State + Build State
**Version:** 2.0 — Full App (Budget Tracker + Canadian FIRE Module, Unified)
**Stack:** Python · Streamlit · SQLite → PostgreSQL (v2)
**Methodology:** `vibe_coding_prompt.md` — Idea State → Spec State → Build State
**Source docs:** `Financial_GPS_Project_Vision.md` · `financial_gps_spec.md` · `financial_gps_canadian_fire_spec.md`

---

## 1. Product Understanding

Financial GPS is a humorous financial decision simulator for Canadian professionals aged 25–45. It combines a transaction-based budget tracker (CSV import, categorization, spending dashboards) with a Canadian FIRE planning engine (TFSA/RRSP/FHSA room tracking, CPP/OAS modeling, Ontario tax, decumulation sequencing) in a single unified app.

The budget tracker answers: **"Where is my money going?"**
The FIRE Planner answers: **"When can I stop working, and what happens if I change course?"**

Both are connected by a hybrid data bridge: CSV transactions seed the FIRE Planner with real spending and income numbers, which the user can review and override. One app. One sidebar. One coherent picture.

---

## 2. Architecture Decision: Three-Layer Stack

```
┌─────────────────────────────────────────────┐
│  L3 — Streamlit UI                          │  Pages, components, narrator
├─────────────────────────────────────────────┤
│  L2 — App Services                          │  Budget logic, hybrid bridge,
│        budget/  ·  bridge/  ·  fire/        │  FIRE engine calls
├─────────────────────────────────────────────┤
│  L1 — fire_engine/ (pure Python, no UI)     │  Tax, benefits, accounts,
│        calculators/  ·  engine/  ·  params/ │  decumulation, projection
└─────────────────────────────────────────────┘
         ↑ tested independently
```

**Critical rule:** L1 (`fire_engine/`) never imports Streamlit. L3 never calls L1 directly — always through L2 service functions. This boundary makes the engine testable and the UI swappable.

---

## 3. Feature Architecture

### 3.1 MVP Core Features

| # | Feature | Module | Value | Complexity | Depends On |
|---|---|---|---|---|---|
| 1 | CSV Import (RBC + CC) | budget/ | Gets real data in without bank API | Low | None |
| 2 | Transaction Categorization | budget/ | Spending visibility | Medium | CSV Import |
| 3 | Transfer Detection + Deduplication | budget/ | Clean spending totals | Medium | CSV Import |
| 4 | Split / Cash / Offset Transactions | budget/ | Accurate categorization | Medium | Categorization |
| 5 | Home Dashboard | pages/ | At-a-glance financial health | Medium | Transactions + Goals |
| 6 | Spending Dashboard | pages/ | Understand current behaviour | Medium | Categorization |
| 7 | Goals | pages/ | Motivates saving | Medium | Forecasting |
| 8 | Basic Forecast (3-band) | budget/ | 30-year projection | Medium | Income + Expenses |
| 9 | What-If Engine (4 scenarios) | budget/ | Core GPS differentiator | High | Forecast |
| 10 | Humorous Narrator | shared/ | Engagement + retention | Low | All data events |
| 11 | Auth (email/password) | auth/ | Multi-session | Low | None |
| 12 | FIRE Planner — Onboarding | pages/ | Seeds FIRE from real data | Medium | CSV Import |
| 13 | FIRE Account Room Tracker | fire_engine/ | TFSA/RRSP/FHSA accuracy | Medium | FIRE Onboarding |
| 14 | FIRE Benefits Workspace | fire_engine/ | CPP/OAS/GIS modeling | Medium | FIRE Onboarding |
| 15 | FIRE Tax Engine (Fed + Ontario) | fire_engine/ | Honest after-tax numbers | High | Benefits |
| 16 | FIRE Decumulation Sequencer | fire_engine/ | Optimal withdrawal order | High | Tax Engine |
| 17 | FIRE 40-Year Projection | fire_engine/ | Explainable FIRE forecast | High | All L1 |
| 18 | FIRE Scenario Comparison | pages/ | Side-by-side what-if | High | FIRE Projection |
| 19 | Data Quality Panel | pages/ | Flags missing/uncertain data | Low | All |
| 20 | Hybrid Data Bridge | bridge/ | CSV → FIRE defaults | Medium | CSV + FIRE |

### 3.2 Secondary Features (V1.5)

| Feature | Module | Complexity |
|---|---|---|
| Life Timeline (drag events) | pages/ | High |
| Future Self Narrator (AI) | shared/ | Medium |
| Gamification / Achievements | shared/ | Medium |
| FIRE Scenario side-by-side | pages/ | Medium |
| Subscription Hunter | budget/ | Medium |
| Manual transaction entry | budget/ | Low |
| RRIF minimum withdrawal (age 72+) | fire_engine/ | Medium |
| Pension income splitting (couples) | fire_engine/ | High |

### 3.3 Future Roadmap (V2–V3)

| Feature | Version |
|---|---|
| PostgreSQL + Supabase | V2 |
| Multi-user / couples mode | V2 |
| Provincial tax (BC, AB, etc.) | V2 |
| Monte Carlo simulation | V2 |
| Quebec / QPP native mode | V3 |
| AI natural language questions | V3 |
| Open banking / Plaid | V3 |
| Corporate / holdco planning | V3 |
| CRA / Service Canada imports | V3 |

---

## 4. Navigation Structure

```
Streamlit Sidebar
├── 🏠  Home
├── 💸  Spending
├── 📈  Forecast
├── 🔀  Scenarios
├── 🎯  Goals
├── 🔥  FIRE Planner          ← NEW
│   ├── Financial Profile
│   ├── Account Room Tracker
│   ├── Benefits Workspace
│   └── FIRE Goal Setup
└── ⚙️  Settings
```

The FIRE Planner sits between Goals and Settings — it's a distinct planning mode, not buried inside Forecast. A user who never touches FIRE Planner gets the same budget-tracker experience as before.

---

## 5. Screen List

```
 1. Login / Register
 2. Onboarding (income + first CSV import + FIRE profile prompt)
 3. Home Dashboard
 4. Spending Dashboard
 5. Forecast Dashboard (basic 3-band)
 6. Scenarios List
 7. Scenario Builder — New Job
 8. Scenario Builder — Buy a House
 9. Scenario Builder — Side Hustle
10. Scenario Builder — Major Purchase
11. Scenario Results / Comparison
12. Goals List
13. Goal Detail / Edit
14. FIRE Planner — Financial Profile       ← NEW
15. FIRE Planner — Account Room Tracker   ← NEW
16. FIRE Planner — Benefits Workspace     ← NEW
17. FIRE Planner — FIRE Goal Setup        ← NEW
18. FIRE Forecast (40-year, drillable)    ← NEW
19. FIRE Scenario Builder                 ← NEW
20. FIRE Scenario Comparison              ← NEW
21. Data Quality Panel                    ← NEW
22. Settings (profile, income, assumptions, FIRE assumptions)
23. Transaction Detail (split / offset / cash)
24. Categorization Rules
```

---

## 6. UX Flows

### 6.1 New User Flow (Budget Tracker Path)
```
Register → Onboarding
  → Set income
  → Import CSV
  → Review categories
  → Home Dashboard
    → Spending (understand now)
    → Forecast (see future)
    → Scenarios (ask what-if)
    → Goals (set targets)
```

### 6.2 New User Flow (FIRE Path — same onboarding, extended)
```
Register → Onboarding
  → Set income + province + DOB
  → Import CSV
  → [FIRE Prompt] "Want to set up your FIRE Planner? Takes 2 minutes."
      → FIRE Financial Profile (account balances, room snapshots)
      → Benefits Workspace (CPP/OAS start-age elections)
      → FIRE Goal Setup (FIRE variant, target date, spending floor)
  → FIRE Forecast (40-year projection, drillable)
    → FIRE Scenario Builder → Compare → Save
```

### 6.3 Hybrid Bridge Flow (Critical Path)
```
CSV Import completes
  ↓
bridge/data_bridge.py runs:
  1. avg_monthly_income    = mean of last 3 months' income transactions
  2. avg_monthly_spending  = mean of last 3 months' expenses by category
  3. Write to fire_profile.income_source_defaults[]
  4. Write to fire_profile.spending_baseline_defaults{}

User opens FIRE Financial Profile:
  → Sees pre-filled income and spending from CSV
  → Banner: "These numbers come from your last 3 months of transactions.
             Edit anything that doesn't reflect your typical month."
  → Editable fields; overrides stored in fire_profile.overrides{}
  → FIRE engine always reads: override if set, else CSV-derived default
```

---

## 7. Complete Data Model

### 7.1 Budget Tracker Tables (from `financial_gps_spec.md`, unchanged)

#### `users`
```sql
id              INTEGER PRIMARY KEY
email           TEXT UNIQUE NOT NULL
password_hash   TEXT NOT NULL
name            TEXT
created_at      DATETIME
```

#### `accounts`
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER FK → users
name            TEXT          -- "RBC Chequing", "Visa Infinite"
type            TEXT          -- chequing | savings | credit | investment
balance         REAL
is_imported     BOOLEAN
created_at      DATETIME
```

#### `transactions`
```sql
id                  INTEGER PRIMARY KEY
user_id             INTEGER FK → users
account_id          INTEGER FK → accounts
date                DATE
description         TEXT
amount              REAL              -- negative = expense, positive = income
category            TEXT
transaction_type    TEXT              -- expense | income | transfer_out | transfer_in |
                                      -- cc_payment | cash_out | cash_in | internal
is_recurring        BOOLEAN
is_excluded         BOOLEAN DEFAULT 0
transfer_match_id   INTEGER FK → transactions
split_group_id      INTEGER FK → split_groups
cash_offset_id      INTEGER FK → cash_offsets
source              TEXT              -- csv_import | manual
raw_description     TEXT
```

#### `category_rules`
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER FK → users
keyword         TEXT
category        TEXT
priority        INTEGER
source          TEXT              -- system | user
created_at      DATETIME
```

#### `goals`
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER FK → users
name            TEXT
target_amount   REAL
current_amount  REAL
monthly_contribution REAL
target_date     DATE
goal_type       TEXT              -- emergency | house | vacation | retirement | other
created_at      DATETIME
```

#### `scenarios`
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER FK → users
name            TEXT
scenario_type   TEXT              -- new_job | buy_house | side_hustle | major_purchase | fire
inputs          JSON
outputs         JSON
created_at      DATETIME
```

#### `split_groups` / `cash_offsets`
```sql
-- (unchanged from financial_gps_spec.md)
```

### 7.2 FIRE Module Tables (new)

#### `fire_profiles`
```sql
id                  TEXT PRIMARY KEY    -- uuid
user_id             INTEGER FK → users UNIQUE
province            TEXT                -- 'ON', 'BC', 'AB' etc.
date_of_birth       DATE
is_canadian_resident BOOLEAN DEFAULT 1
years_in_canada_post_18 INTEGER
is_quebec           BOOLEAN DEFAULT 0
fire_variant        TEXT                -- lean | coast | barista | fat
target_retire_year  INTEGER
spending_floor      REAL
spending_ceiling    REAL
created_at          DATETIME
updated_at          DATETIME
```

#### `fire_income_sources`
```sql
id              TEXT PRIMARY KEY
user_id         INTEGER FK → users
source_type     TEXT            -- employment | self_employment | rental | investment
annual_amount   REAL
income_character TEXT            -- employment | eligible_dividend | non_eligible_dividend |
                                  -- capital_gain | rental | other
start_year      INTEGER
end_year        INTEGER          -- NULL = ongoing
inflation_rate  REAL DEFAULT 0.03
is_pensionable  BOOLEAN DEFAULT 1
is_override     BOOLEAN DEFAULT 0  -- true = user manually set, false = CSV-derived
csv_derived_at  DATETIME           -- when bridge last wrote this value
```

#### `fire_spending_baseline`
```sql
id              TEXT PRIMARY KEY
user_id         INTEGER FK → users
category        TEXT            -- matches transaction category enum
monthly_amount  REAL
inflation_rate  REAL DEFAULT 0.025
is_essential    BOOLEAN
is_override     BOOLEAN DEFAULT 0   -- true = user edited, false = CSV-derived
csv_derived_at  DATETIME
```

#### `fire_investment_accounts`
```sql
id              TEXT PRIMARY KEY
user_id         INTEGER FK → users
account_type    TEXT            -- TFSA | RRSP | FHSA | RRIF | taxable | HISA
current_balance REAL
opened_date     DATE
institution     TEXT
beneficiary_type TEXT
```

#### `fire_account_room_history`
```sql
id              TEXT PRIMARY KEY
account_id      TEXT FK → fire_investment_accounts
event_date      DATE
event_type      TEXT            -- contribution | withdrawal | room_added | room_restored
amount          REAL
room_after      REAL
notes           TEXT
```

#### `fire_tfsa_room_state`
```sql
user_id                 INTEGER FK → users PRIMARY KEY
snapshot_year           INTEGER
prior_unused_room       REAL
annual_limit            REAL
prior_year_withdrawals  REAL
ytd_contributions       REAL
available_room          REAL    -- computed
was_non_resident        BOOLEAN DEFAULT 0
```

#### `fire_rrsp_room_state`
```sql
user_id                     INTEGER FK → users PRIMARY KEY
snapshot_year               INTEGER
prior_unused_room           REAL
prior_year_earned_income    REAL
annual_rrsp_max             REAL
pension_adjustment          REAL DEFAULT 0
par_amount                  REAL DEFAULT 0
pspa_amount                 REAL DEFAULT 0
deduction_limit             REAL    -- computed
ytd_contributions           REAL
```

#### `fire_fhsa_state`
```sql
user_id                     INTEGER FK → users PRIMARY KEY
account_id                  TEXT FK → fire_investment_accounts
open_date                   DATE
is_first_time_buyer         BOOLEAN DEFAULT 1
annual_room                 REAL DEFAULT 8000
carryforward_room           REAL DEFAULT 0
lifetime_participation_room REAL DEFAULT 40000
qualifying_withdrawal_date  DATE
closure_status              TEXT    -- open | closed_withdrawal | closed_transfer | expired
post_closure_destination    TEXT    -- RRSP | RRIF | taxable
```

#### `fire_benefit_enrollments`
```sql
id                      TEXT PRIMARY KEY
user_id                 INTEGER FK → users
benefit_type            TEXT        -- CPP | OAS | GIS
elected_start_age       INTEGER
estimated_monthly_amount REAL
source                  TEXT        -- user_estimate | calculated
cpp_estimate_at_65      REAL
oas_years_resident      INTEGER
```

#### `fire_projection_years`
```sql
id                  TEXT PRIMARY KEY
scenario_id         TEXT FK → scenarios
year                INTEGER
-- Income
employment_income   REAL
cpp_received        REAL
oas_received        REAL
gis_received        REAL
investment_income   REAL
-- Tax
federal_tax         REAL
provincial_tax      REAL
oas_recovery_tax    REAL
effective_rate      REAL
-- Accounts
tfsa_balance        REAL
rrsp_balance        REAL
fhsa_balance        REAL
taxable_balance     REAL
-- Cash flow
total_income        REAL
total_spending      REAL
net_surplus         REAL
net_worth           REAL
-- Audit
triggered_rules     JSON    -- list of rule strings fired this year
sequencer_notes     JSON    -- decumulation explanation per year
```

#### `forecast_assumptions`
```sql
id                              TEXT PRIMARY KEY
version                         TEXT
effective_date                  DATE    -- quarterly for OAS/GIS, annual for brackets
mode                            TEXT    -- conservative | expected | optimistic
inflation_general               REAL
inflation_housing               REAL
equity_return                   REAL
bond_return                     REAL
tfsa_annual_limits              JSON    -- {2024: 7000, 2025: 7000, 2026: 7000}
rrsp_annual_max                 JSON    -- {2025: 32490, 2026: 33810}
cpp_ympe                        REAL    -- $74,600 (2026)
cpp2_yampe                      REAL    -- $85,000 (2026)
cpp_max_monthly_at_65           REAL
oas_max_monthly_65_74           REAL    -- quarterly value
oas_max_monthly_75_plus         REAL    -- quarterly value
oas_recovery_threshold          REAL    -- $95,323 (2026)
gis_earned_income_full_exempt   REAL    -- $5,000 (2026)
gis_earned_income_partial_exempt REAL   -- $10,000 (2026)
gis_single_threshold            REAL
gis_couple_threshold            REAL
```

### 7.3 Key Relationships

```
users
  ├── accounts (1:many)
  │     └── transactions (1:many)
  ├── category_rules (1:many)
  ├── goals (1:many)
  ├── scenarios (1:many)
  │     └── fire_projection_years (1:many)  ← FIRE scenarios only
  ├── fire_profiles (1:1)
  ├── fire_income_sources (1:many)
  ├── fire_spending_baseline (1:many)
  ├── fire_investment_accounts (1:many)
  │     └── fire_account_room_history (1:many)
  ├── fire_tfsa_room_state (1:1)
  ├── fire_rrsp_room_state (1:1)
  ├── fire_fhsa_state (1:1)
  └── fire_benefit_enrollments (1:many)
```

---

## 8. The Hybrid Bridge (Critical Design)

### 8.1 What it Does

`bridge/data_bridge.py` runs after every CSV import and produces FIRE defaults from real transaction data. It never overwrites user overrides.

### 8.2 Bridge Logic

```python
def sync_fire_defaults(user_id: int, db: Connection) -> BridgeResult:
    """
    Called after every successful CSV import.
    Reads last 90 days of transactions.
    Writes to fire_income_sources and fire_spending_baseline
    only where is_override = False.
    """

    # 1. Calculate monthly income from non-excluded income transactions
    income_txns = get_transactions(user_id, days=90, type="income", excluded=False)
    avg_monthly_income = sum(t.amount for t in income_txns) / 3

    # 2. Calculate monthly spending by category
    expense_txns = get_transactions(user_id, days=90, type="expense", excluded=False)
    by_category = defaultdict(float)
    for t in expense_txns:
        by_category[t.category] += abs(t.amount)
    avg_by_category = {cat: total / 3 for cat, total in by_category.items()}

    # 3. Write income — skip if user has manually overridden
    existing_income = get_fire_income_source(user_id, source_type="employment")
    if not existing_income or not existing_income.is_override:
        upsert_fire_income_source(user_id, {
            "source_type": "employment",
            "annual_amount": avg_monthly_income * 12,
            "income_character": "employment",
            "is_override": False,
            "csv_derived_at": now()
        })

    # 4. Write spending by category — skip overridden rows
    for category, monthly_amount in avg_by_category.items():
        existing = get_fire_spending_baseline(user_id, category)
        if not existing or not existing.is_override:
            upsert_fire_spending_baseline(user_id, {
                "category": category,
                "monthly_amount": monthly_amount,
                "is_override": False,
                "csv_derived_at": now()
            })

    return BridgeResult(income_synced=True, categories_synced=len(avg_by_category))
```

### 8.3 How FIRE Engine Reads Data

```python
def get_fire_income(user_id: int, db: Connection) -> float:
    """
    Returns annual income for FIRE projection.
    Priority: user override > CSV-derived > 0 (with warning flag).
    """
    source = get_fire_income_source(user_id, source_type="employment")
    if source:
        return source.annual_amount
    return 0.0  # triggers Data Quality Panel warning

def get_fire_spending(user_id: int, db: Connection) -> dict:
    """
    Returns monthly spending by category.
    Priority: user override > CSV-derived > empty (with warning flag).
    """
    rows = get_fire_spending_baseline(user_id)
    return {row.category: row.monthly_amount for row in rows}
```

### 8.4 UI Treatment of Bridge Data

On the FIRE Financial Profile screen:
- Fields derived from CSV show a subtle `📊 From your transactions` badge
- Fields manually overridden show a `✏️ Edited` badge
- A "Reset to transactions" link appears on overridden fields
- If no CSV has been imported: fields are empty with a banner:
  *"Import your bank CSV to pre-fill these fields — or enter them manually."*

---

## 9. Folder Structure

```
financial_gps/
│
├── app.py                      ← Streamlit entry point; sidebar nav
│
├── auth/
│   ├── login.py
│   └── register.py
│
├── pages/                      ← Streamlit page modules (L3)
│   ├── home.py
│   ├── spending.py
│   ├── forecast.py
│   ├── scenarios.py
│   ├── goals.py
│   ├── fire_profile.py         ← FIRE Financial Profile screen
│   ├── fire_room_tracker.py    ← TFSA/RRSP/FHSA room display
│   ├── fire_benefits.py        ← CPP/OAS/GIS workspace
│   ├── fire_goal_setup.py      ← FIRE variant + target date
│   ├── fire_forecast.py        ← 40-year projection + drillable rows
│   ├── fire_scenarios.py       ← FIRE scenario builder + comparison
│   ├── data_quality.py         ← Data Quality Panel
│   └── settings.py
│
├── budget/                     ← L2 budget services
│   ├── csv_parser.py
│   ├── categorizer.py
│   ├── transfer_detector.py
│   ├── split_engine.py
│   ├── cash_tracker.py
│   ├── offset_engine.py
│   ├── forecaster.py           ← basic 3-band forecast (not FIRE)
│   ├── scenario_engine.py      ← What-If engine (4 scenarios)
│   └── narrator.py             ← humorous message generator
│
├── bridge/                     ← L2 hybrid data bridge
│   ├── data_bridge.py          ← sync_fire_defaults()
│   └── bridge_status.py        ← last sync time, coverage report
│
├── fire_engine/                ← L1 pure Python FIRE engine (no Streamlit)
│   ├── __init__.py
│   ├── models/
│   │   ├── household.py
│   │   ├── person.py
│   │   ├── income_source.py
│   │   ├── investment_account.py
│   │   ├── benefit_enrollment.py
│   │   ├── life_event.py
│   │   └── tax_result.py
│   ├── calculators/
│   │   ├── tfsa_room.py
│   │   ├── rrsp_room.py
│   │   ├── fhsa_state.py
│   │   ├── cpp_estimator.py
│   │   ├── oas_estimator.py
│   │   ├── gis_estimator.py    ← earned-income exemption included
│   │   ├── federal_tax.py      ← (income × R) − K method
│   │   ├── provincial_tax_on.py ← brackets + surtax + health premium + reduction
│   │   └── decumulation.py     ← marginal-rate-aware waterfall sequencer
│   ├── engine/
│   │   ├── projection.py       ← 40-year deterministic loop
│   │   ├── scenario.py         ← clone, override, compare
│   │   └── rules.py            ← rule registry
│   └── parameters/
│       ├── cra_2024.py
│       ├── cra_2025.py         ← mid-year 14.5% rate handled
│       ├── cra_2026.py         ← confirmed from CRA T4032-ON 2026
│       └── loader.py           ← get_params(year, province, effective_date)
│
├── shared/
│   ├── db.py                   ← SQLite connection + schema init
│   ├── models.py               ← shared dataclasses/DTOs
│   └── utils.py
│
└── tests/
    ├── calculators/
    │   ├── test_tfsa_room.py
    │   ├── test_rrsp_room.py
    │   ├── test_fhsa_state.py
    │   ├── test_federal_tax.py         ← CRA T4032 regression cases
    │   ├── test_provincial_tax_on.py   ← CRA T4032 regression cases
    │   ├── test_gis_estimator.py       ← earned-income exemption cases
    │   └── test_decumulation.py        ← sequencer regression cases
    ├── bridge/
    │   └── test_data_bridge.py
    ├── engine/
    │   └── test_projection.py
    └── fixtures/
        ├── household_single_ontario.json
        ├── household_couple_gis_eligible.json
        └── household_bracket_gap_year.json
```

---

## 10. Key Screen Specs

### Home Dashboard
- KPI cards: Net Worth / Savings Rate / Monthly Surplus / Months to Next Goal
- If FIRE profile complete: add **FIRE Date** KPI card ("On track for 2041")
- Narrator message (context-aware)
- Mini forecast sparkline (12-month)
- Goal progress bars (top 3)

### Spending Dashboard
- Donut chart: spending by category (current month)
- Bar chart: monthly trend (12 months)
- Top 10 transactions table
- Subscription Hunter badge
- Narrator: spending-context messages

### Forecast Dashboard (Basic)
- 30-year 3-band line chart (Conservative / Expected / Optimistic)
- Milestone markers
- Editable assumptions panel (return rate, inflation, income growth)
- CTA: *"For a Canada-specific FIRE projection, open the FIRE Planner →"*

### FIRE Financial Profile
- Income section: annual employment income, income character selector
  - Badge: `📊 From your transactions` or `✏️ Edited` per field
  - "Reset to transactions" link on overridden fields
- Spending section: monthly amounts by category, editable
  - Same badge treatment
- Account balances: TFSA / RRSP / FHSA / Taxable / HISA
- Province selector, DOB, residency flag
- Data Quality Panel CTA if warnings exist

### FIRE Account Room Tracker
- TFSA: available room, YTD contributions, Jan 1 restoration amount, warning if near limit
- RRSP: deduction limit, YTD contributions, age-71 flag if applicable
- FHSA: participation room, carryforward, expiry countdown if open
- All rooms editable with a "Verify with CRA My Account" prompt

### FIRE Benefits Workspace
- CPP: start age slider (60–70), live monthly amount preview, start date
- OAS: deferral toggle (65–70), partial pension flag (years in Canada / 40), live preview
- GIS: auto-calculated based on projected income, flagged if eligible
- Narrator: *"Delaying CPP to 70 adds $X/month. Future You is taking notes."*

### FIRE 40-Year Forecast
- Net worth line chart (Conservative / Expected / Optimistic)
- FIRE date marker on chart
- Year-by-year drillable table:
  each row expands to show: income sources, tax (federal + Ontario), benefits, account activity, triggered rules, sequencer notes
- Data Quality Panel warnings inline if gaps exist

### Data Quality Panel
| Warning | Trigger |
|---|---|
| TFSA room unverified | No manual room entry |
| CPP estimate missing | No Service Canada import or manual entry |
| No CSV imported | FIRE spending derived from manual entry only |
| Province not set | fire_profile.province is NULL |
| ACB unknown for taxable accounts | taxable account with no ACB entered |
| OAS threshold proximity | Projected income within $15K of $95,323 |
| FHSA expiry warning | < 2 years to 15-year lifetime cap |
| RRSP age-71 approaching | Person turns 71 within 2 years |

---

## 11. What-If Engine (Budget Layer)

### Scenario Types and Inputs

**New Job**
- Current salary → New salary
- Commute cost change
- Benefits value change (extended health, pension)
- Remote work savings (transport, lunches)

**Buy a House**
- Purchase price, down payment %
- Mortgage rate, amortization
- Property tax (annual)
- Maintenance reserve (1% of value/year default)
- Current rent (eliminated)

**Side Hustle**
- Monthly revenue
- Monthly expenses
- Growth rate assumption
- Tax rate on self-employment income

**Major Purchase**
- Purchase price
- Funded by: savings | financing | mixed
- If financed: rate + term

### Scenario Output Cards
- Monthly cash flow delta
- 5-year net worth impact
- Goal date acceleration / delay
- Narrator verdict

---

## 12. Narrator Message Library

### Budget Events
| Trigger | Message |
|---|---|
| High dining spend | "You spent $X on takeout this month. Your future house fund would like a brief word." |
| Subscription detected | "Found N recurring charges. One of them you forgot existed. You're welcome." |
| Salary increase scenario | "Congratulations. Future You approves of this salary increase." |
| Major purchase | "Financial impact: Moderate. Emotional impact: Extremely shiny." |
| Goal on track | "On pace. Future You is cautiously optimistic." |
| Goal behind | "You're $X behind on your Emergency Fund. Future You has thoughts." |
| First login | "Welcome. Let's figure out where you're actually headed." |
| No goals set | "Future You is waiting for direction. What are we even doing this for?" |
| Scenario saved | "Saved. Future You is watching this one closely." |

### FIRE Events
| Trigger | Message |
|---|---|
| FIRE date calculated | "Projected retirement: [Year]. The fifth monitor remains under review." |
| CPP delay benefit shown | "Delaying CPP to 70 adds $X/month. Future You took the deal." |
| OAS recovery risk | "Congratulations on your income. The government would like 15 cents of every dollar above $95,323." |
| GIS eligibility detected | "You qualify for GIS. The bad news is what that means about your income. Let's fix that." |
| TFSA over-contribution risk | "Contributing this would cost 1% per month in penalties. Future You would prefer you didn't." |
| FHSA expiry approaching | "Your FHSA expires in 2 years. It would like to become an RRSP before then." |
| CSV synced to FIRE | "Your transactions updated your FIRE baseline. Review anything that looks off." |

### Tone Rules (unchanged)
- Never mention a dollar amount without context
- Never use the word "budget"
- Never say "Great job!" or hollow affirmations
- Always reference consequences, not judgments
- Humor is dry, not zany

---

## 13. Edge Cases & Risks

### Budget Tracker (from `financial_gps_spec.md`, unchanged)
| Risk | Mitigation |
|---|---|
| Unknown CSV format | Show raw preview, let user map columns |
| Duplicate transactions | Hash (date + amount + description + account_id), skip dupes |
| CC payments double-counted | Transfer detector auto-matches + excludes |
| French characters in RBC descriptions | UTF-8 decode, strip for categorizer |
| Categorization conflicts | User rules always win over system rules |

### Hybrid Bridge
| Risk | Mitigation |
|---|---|
| Only 1 month of CSV data | Use available data; warn "Based on 1 month — consider importing more history" |
| Income transaction misclassified as expense | Re-runs after category correction; user can trigger manual re-sync |
| User imports CSV after manually editing FIRE profile | Only updates non-overridden fields; shows "N fields updated, M fields preserved (edited)" |
| No CSV imported at all | FIRE profile shows empty state with manual entry option; no bridge sync attempted |

### FIRE Engine
| Risk | Mitigation |
|---|---|
| Province not set | Block projection; prompt user before running any calculation |
| CPP estimate missing | Use CRA maximum × 70% as a noted estimate; flag in Data Quality Panel |
| TFSA room unverified | Run projection but add ±$X uncertainty note to TFSA balance in results |
| OAS threshold proximity | Add warning note to sequencer output in drillable rows |
| RRSP age-71 hit mid-projection | Rule fires; projection converts to RRIF withdrawal; note in triggered_rules |
| Quebec user | Block FIRE Planner; show "Quebec support coming soon" message |

---

## 14. CRA Parameters (Verified 2026, from CRA T4032-ON)

> Source: Official CRA T4032 Ontario Payroll Deductions Guide, 2026 edition. Re-verify each January.

### Federal Tax (Rate × Income − Constant K)
| Income From | Income To | Rate (R) | Constant (K) |
|---|---|---|---|
| $0 | $58,523 | 14.00% | $0 |
| $58,523 | $117,045 | 20.50% | $3,804 |
| $117,045 | $181,440 | 26.00% | $10,241 |
| $181,440 | $258,482 | 29.00% | $15,685 |
| $258,482 | and over | 33.00% | $26,024 |

- BPA: $16,452 max / $14,829 floor (phases out $181,440–$258,482)
- Lowest rate for credit calc: 14%

### Ontario Provincial Tax (Rate × Income − Constant KP)
| Income From | Income To | Rate (V) | Constant (KP) |
|---|---|---|---|
| $0 | $53,891 | 5.05% | $0 |
| $53,891 | $107,785 | 9.15% | $2,210 |
| $107,785 | $150,000 | 11.16% | $4,376 |
| $150,000 | $220,000 | 12.16% | $5,876 |
| $220,000 | and over | 13.16% | $8,076 |

- Ontario BPA: $12,989
- Surtax tier 1: 20% on provincial tax > $5,818
- Surtax tier 2: +36% on provincial tax > $7,446
- Health Premium: $0–$900 banded by taxable income (see §12.2)
- Low-income reduction: $300 personal amount base

### CRA Regression Test Cases (gold standard — must match exactly)
| Income | Federal | Ontario (incl. surtax + premium) | Total |
|---|---|---|---|
| $62,798.84 | $5,957.85 | $3,264.26 | $9,222.11 |
| $79,872.00 | $9,406.39 | $4,957.90 | $14,364.29 |

### Accounts & Benefits
| Parameter | 2026 Value |
|---|---|
| TFSA annual limit | $7,000 |
| TFSA cumulative (since 2009) | $109,000 |
| RRSP max | $33,810 |
| FHSA annual | $8,000 / $40,000 lifetime |
| CPP YMPE (tier 1) | $74,600 |
| CPP YAMPE (tier 2 / CPP2) | $85,000 |
| CPP contribution rate | 5.95% employee (11.9% self-employed) |
| CPP2 rate | 4.00% on earnings $74,600–$85,000 |
| OAS max (65–74) | ~$751.97/mo (Q3 2026) — quarterly indexed |
| OAS max (75+) | ~$827.17/mo (Q3 2026) — quarterly indexed |
| OAS recovery threshold | $95,323 (2026 net income) |
| GIS earned income exempt (full) | $5,000 |
| GIS earned income exempt (50%) | next $10,000 |
| Capital gains inclusion rate | 50% |
| Eligible dividend gross-up | 38% |
| Non-eligible dividend gross-up | 15% |

---

## 15. MVP Build Plan

> Follows `vibe_coding_prompt.md` phasing: Foundation → Data In → Services → UI.
> L1 gate rule: no Streamlit page is written until the L1 engine passes all regression tests.

### Phase 0 — Foundation (Day 1–2)
- [ ] Repo init + `requirements.txt` (streamlit, pandas, plotly, streamlit-authenticator, bcrypt)
- [ ] `shared/db.py`: schema init for ALL tables (budget + FIRE) on startup
- [ ] `auth/`: register + login
- [ ] Sidebar navigation skeleton (all nav items, empty pages)
- [ ] Deploy shell to Streamlit Community Cloud
- [ ] `fire_engine/parameters/cra_2026.py`: all verified values from §14
- [ ] `fire_engine/parameters/loader.py`: quarterly OAS/GIS resolution + effective_date support

### Phase 1 — Budget: Data In (Day 3–6)
- [ ] `budget/csv_parser.py`: RBC chequing + credit card + multi-account detection
- [ ] Account naming prompt UI
- [ ] `budget/categorizer.py`: keyword engine + 50+ keyword starter map
- [ ] Transaction review UI
- [ ] `budget/transfer_detector.py`: CC payment auto-match
- [ ] Ghost account + warning banner

### Phase 1b — Budget: Transaction Intelligence (Day 7–10)
- [ ] `budget/split_engine.py`
- [ ] `budget/cash_tracker.py`
- [ ] `budget/offset_engine.py`
- [ ] Categorization rules settings page
- [ ] **After Phase 1b completes:** `bridge/data_bridge.py` — sync_fire_defaults() first run

### Phase 2 — Budget: Dashboards (Day 11–14)
- [ ] `pages/spending.py`: donut + bar + top transactions + subscription hunter
- [ ] `pages/home.py`: net worth + savings rate + surplus + sparkline + goals
- [ ] `pages/goals.py`: CRUD + completion date + required monthly savings
- [ ] `pages/forecast.py`: basic 3-band 30-year projection
- [ ] `budget/narrator.py`: budget event message library

### Phase 3 — Budget: What-If Engine (Day 15–18)
- [ ] `budget/scenario_engine.py`: 4 scenario calculators
- [ ] `pages/scenarios.py`: wizard builders + results + save/load
- [ ] Narrator: scenario-specific verdicts

### Phase 4 — FIRE: L1 Engine (Day 19–24)
> **Gate: all tests must pass before Phase 5 begins**
- [ ] `fire_engine/models/`: all dataclasses
- [ ] `fire_engine/calculators/tfsa_room.py` + tests
- [ ] `fire_engine/calculators/rrsp_room.py` + tests
- [ ] `fire_engine/calculators/fhsa_state.py` + tests
- [ ] `fire_engine/calculators/federal_tax.py` + CRA regression tests
- [ ] `fire_engine/calculators/provincial_tax_on.py` + CRA regression tests ← gate
- [ ] `fire_engine/calculators/cpp_estimator.py` + tests
- [ ] `fire_engine/calculators/oas_estimator.py` + tests
- [ ] `fire_engine/calculators/gis_estimator.py` + earned-income exemption tests
- [ ] `fire_engine/calculators/decumulation.py` + sequencer regression tests
- [ ] `fire_engine/engine/rules.py`: full rule registry
- [ ] `fire_engine/engine/projection.py`: 40-year deterministic loop
- [ ] 40-year integration test with fixture households

### Phase 5 — FIRE: UI Screens (Day 25–29)
- [ ] `pages/fire_profile.py`: income + spending (with CSV badge treatment)
- [ ] `pages/fire_room_tracker.py`: TFSA/RRSP/FHSA display + edit
- [ ] `pages/fire_benefits.py`: CPP/OAS sliders + live preview
- [ ] `pages/fire_goal_setup.py`: FIRE variant + target date + spending floor
- [ ] `pages/fire_forecast.py`: 40-year chart + drillable year table
- [ ] `pages/data_quality.py`: all warning flags

### Phase 6 — FIRE: Scenarios + Bridge Polish (Day 30–32)
- [ ] `fire_engine/engine/scenario.py`: clone + override + compare
- [ ] `pages/fire_scenarios.py`: FIRE scenario builder + comparison
- [ ] Bridge: re-sync trigger after each CSV import
- [ ] Bridge: "N fields updated, M preserved" notification
- [ ] Home Dashboard: FIRE Date KPI card (if profile complete)

### Phase 7 — Polish + Onboarding (Day 33–35)
- [ ] Onboarding: name → income → CSV import → FIRE profile prompt
- [ ] Empty states for all screens (narrator nudges)
- [ ] Full narrator message library (budget + FIRE)
- [ ] Mobile layout audit (single-column)
- [ ] Settings page: profile + tax assumptions + FIRE assumptions
- [ ] README + deploy docs

### Phase 8 — Beta Hardening + Deployment Validation
- [ ] Use checked-in sample CSVs for repeatable Streamlit smoke testing
- [ ] Add regression coverage for sample CSV parsing, import, transfer matching, dashboard totals, and bridge sync
- [ ] Tighten deployment hygiene: secrets ignored, sample data documented, SQLite limitations clear
- [ ] Run deployed-app beta path with a fresh account before inviting testers
- [ ] Generate additional synthetic CSVs from the sample structure when new edge cases appear

### Minimum Shippable State
A single Ontario-resident user can:
1. Register and log in
2. Import their RBC and credit card CSVs
3. See spending by category, trends, and top transactions
4. See their net worth, savings rate, and monthly surplus on the home dashboard
5. Set financial goals with completion dates
6. Run a basic 30-year 3-band forecast
7. Ask what-if on a new job, house, side hustle, or major purchase
8. Open the FIRE Planner with their transaction data pre-filled
9. Set their TFSA/RRSP/FHSA balances and room
10. Choose CPP and OAS start ages with live monthly previews
11. See a 40-year FIRE projection with drillable year-by-year breakdown including full federal + Ontario tax
12. Compare two FIRE scenarios side-by-side
13. See the Data Quality Panel with actionable warnings

---

*Methodology: `vibe_coding_prompt.md` · Sources: `Financial_GPS_Project_Vision.md` · `financial_gps_spec.md` · `financial_gps_canadian_fire_spec.md` · CRA T4032-ON 2026*
